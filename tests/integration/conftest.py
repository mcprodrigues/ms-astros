"""
Integration fixtures: real Weaviate (WEAVIATE_URL) and the real embedding model.
Each test session uses its own throwaway collection.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.dependencies import build_container
from app.main import create_app
from app.settings import Settings

API_KEY = "integration-key"


@pytest.fixture(scope="session")
def integration_settings() -> Settings:
    return Settings(
        WEAVIATE_INDEX_NAME=f"AstrosIT{uuid.uuid4().hex[:8]}",
        API_KEY=API_KEY,
        _env_file=None,
    )


@pytest.fixture(scope="session")
def live_container(integration_settings):
    container = build_container(integration_settings)
    yield container
    store = container.document_store_provider.get_document_store()
    store.client.collections.delete(integration_settings.WEAVIATE_INDEX_NAME)
    container.close()


@pytest.fixture
def empty_container(live_container):
    live_container.indexing_pipeline.reset_index()
    return live_container


@pytest.fixture
def live_client(empty_container, integration_settings):
    app = create_app(
        settings=integration_settings,
        container_factory=lambda _s: empty_container,
        bootstrap_index=False,
    )
    # Not used as a context manager: the session fixture owns the connection.
    return TestClient(app, raise_server_exceptions=False).__enter__()
