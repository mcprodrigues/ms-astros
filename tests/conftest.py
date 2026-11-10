import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.fakes import InMemoryStoreProvider, make_container


@pytest.fixture
def store_provider() -> InMemoryStoreProvider:
    return InMemoryStoreProvider()


@pytest.fixture
def container(store_provider):
    return make_container(store_provider)


@pytest.fixture
def client(container):
    app = create_app(container_factory=lambda _settings: container, bootstrap_index=False)
    with TestClient(app) as test_client:
        yield test_client
