def test_reset_goes_through_service_and_empties_index(client):
    client.post("/api/v1/index/movie", json={"titulo": "Lavra dor", "movie_id": "m1"})
    assert client.get("/api/v1/index/count").json()["document_count"] == 1

    response = client.post("/api/v1/index/reset")

    assert response.status_code == 200
    assert client.get("/api/v1/index/count").json()["document_count"] == 0


def test_shutdown_closes_store_connection(container, store_provider):
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app(container_factory=lambda _s: container, bootstrap_index=False)
    with TestClient(app):
        assert store_provider.closed is False
    assert store_provider.closed is True
