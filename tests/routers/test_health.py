def test_ping_is_liveness_only(client, store_provider):
    store_provider.ready = False

    response = client.get("/ping")

    assert response.status_code == 200


def test_readiness_reports_document_count(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "indexed_documents": 0}


def test_readiness_is_503_when_store_unreachable(client, store_provider):
    store_provider.ready = False

    response = client.get("/api/v1/health")

    assert response.status_code == 503


def test_root_level_health_duplicate_was_removed(client):
    assert client.get("/health").status_code == 404
