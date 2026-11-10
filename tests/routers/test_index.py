import pytest

from tests.conftest import AUTH, make_client


def test_reset_goes_through_service_and_empties_index(client):
    client.post("/api/v1/index/movie", json={"titulo": "Lavra dor"}, headers=AUTH)
    assert client.get("/api/v1/index/count").json()["document_count"] == 1

    response = client.post("/api/v1/index/reset", headers=AUTH)

    assert response.status_code == 200
    assert client.get("/api/v1/index/count").json()["document_count"] == 0


def test_shutdown_closes_store_connection(container, settings, store_provider):
    with make_client(settings, container=container):
        assert store_provider.closed is False
    assert store_provider.closed is True


WRITE_ROUTES = [
    ("post", "/api/v1/index/movie", {"json": {"titulo": "X"}}),
    ("post", "/api/v1/index/movie/form", {"data": {"titulo": "X"}}),
    ("post", "/api/v1/index/batch/csv", {"files": {"file": ("c.csv", b"x", "text/csv")}}),
    ("delete", "/api/v1/index/movie/x", {}),
    ("post", "/api/v1/index/reset", {}),
]


@pytest.mark.parametrize(("method", "path", "kwargs"), WRITE_ROUTES)
def test_write_routes_require_api_key(client, method, path, kwargs):
    missing = getattr(client, method)(path, **kwargs)
    wrong = getattr(client, method)(path, headers={"X-API-Key": "nope"}, **kwargs)

    assert missing.status_code == 401
    assert wrong.status_code == 401


@pytest.mark.parametrize(("method", "path", "kwargs"), WRITE_ROUTES)
def test_write_routes_disabled_when_no_key_configured(method, path, kwargs):
    from app.settings import Settings

    with make_client(Settings(_env_file=None)) as no_key_client:
        response = getattr(no_key_client, method)(path, headers=AUTH, **kwargs)

    assert response.status_code == 503


def test_read_routes_are_public(client):
    assert client.get("/api/v1/index/count").status_code == 200
    assert client.post("/api/v1/search/semantic", json={"query": "x"}).status_code == 200


def test_csv_upload_reports_ingestion(client, catalog_csv):
    response = client.post(
        "/api/v1/index/batch/csv",
        files={"file": ("catalogo.csv", catalog_csv.read_bytes(), "text/csv")},
        headers=AUTH,
    )

    assert response.status_code == 200
    body = response.json()
    assert (body["inserted"], len(body["duplicates"]), len(body["invalid_rows"])) == (2, 1, 1)


def test_csv_path_parameter_no_longer_reads_server_files(client):
    response = client.post("/api/v1/index/batch/csv?csv_path=/etc/passwd", headers=AUTH)

    assert response.status_code == 422  # no file uploaded; the path is ignored


def test_csv_upload_rejects_non_csv(client):
    response = client.post(
        "/api/v1/index/batch/csv",
        files={"file": ("catalogo.xlsx", b"PK", "application/vnd.ms-excel")},
        headers=AUTH,
    )

    assert response.status_code == 415


def test_csv_upload_rejects_oversized_file(catalog_csv):
    from app.settings import Settings

    small = Settings(API_KEY="test-key", MAX_UPLOAD_BYTES=10, _env_file=None)
    with make_client(small) as small_client:
        response = small_client.post(
            "/api/v1/index/batch/csv",
            files={"file": ("c.csv", catalog_csv.read_bytes(), "text/csv")},
            headers=AUTH,
        )

    assert response.status_code == 413


def test_csv_upload_with_missing_title_column_is_422(client):
    response = client.post(
        "/api/v1/index/batch/csv",
        files={"file": ("c.csv", b"Sinopse\nalgo\n", "text/csv")},
        headers=AUTH,
    )

    assert response.status_code == 422
    assert "Título Original" in response.json()["detail"]


def test_delete_missing_movie_is_404(client):
    response = client.delete("/api/v1/index/movie/does-not-exist", headers=AUTH)

    assert response.status_code == 404


def test_delete_twice_second_is_404(client):
    client.post("/api/v1/index/movie", json={"titulo": "A", "movie_id": "a"}, headers=AUTH)

    assert client.delete("/api/v1/index/movie/a", headers=AUTH).status_code == 200
    assert client.delete("/api/v1/index/movie/a", headers=AUTH).status_code == 404
