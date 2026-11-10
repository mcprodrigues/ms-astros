from tests.conftest import make_client


def break_store(store_provider):
    def broken(*_args, **_kwargs):
        raise ConnectionError("internal weaviate host 10.0.0.7 refused")

    store_provider.store.count_documents = broken
    store_provider.store.embedding_retrieval = broken
    store_provider.ready = False


def test_store_down_returns_503_without_leaking_internals(client, store_provider):
    break_store(store_provider)

    count = client.get("/api/v1/index/count")
    search = client.post("/api/v1/search/semantic", json={"query": "x"})

    for response in (count, search):
        assert response.status_code == 503
        assert response.json() == {"detail": "Index backend unavailable"}
        assert "10.0.0.7" not in response.text


def test_unexpected_error_is_generic_500(client, container, monkeypatch):
    def boom(**_kwargs):
        raise RuntimeError("secret stack detail")

    monkeypatch.setattr(container.search_pipeline, "search", boom)

    response = client.post("/api/v1/search/semantic", json={"query": "x"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "secret" not in response.text


def test_cors_disabled_by_default(client):
    response = client.options(
        "/api/v1/search/semantic",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )

    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_only_configured_origins_without_credentials():
    from app.settings import Settings

    settings = Settings(CORS_ALLOW_ORIGINS=["https://astros.example"], _env_file=None)
    with make_client(settings) as cors_client:
        allowed = cors_client.options(
            "/api/v1/search/semantic",
            headers={"Origin": "https://astros.example", "Access-Control-Request-Method": "POST"},
        )
        denied = cors_client.options(
            "/api/v1/search/semantic",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
        )

    assert allowed.headers["access-control-allow-origin"] == "https://astros.example"
    assert "access-control-allow-credentials" not in allowed.headers
    assert "access-control-allow-origin" not in denied.headers
