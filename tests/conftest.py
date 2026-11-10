import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings
from tests.fakes import InMemoryStoreProvider, make_container


@pytest.fixture
def store_provider() -> InMemoryStoreProvider:
    return InMemoryStoreProvider()


API_KEY = "test-key"
AUTH = {"X-API-Key": API_KEY}


@pytest.fixture
def settings() -> Settings:
    return Settings(API_KEY=API_KEY, _env_file=None)


@pytest.fixture
def container(store_provider, settings):
    return make_container(store_provider, settings)


def make_client(settings: Settings, store_provider=None, container=None) -> TestClient:
    """
    App wired exactly like production: the container is built from the same
    Settings the app receives. Pass `container` to reuse one a test inspects.
    """

    def factory(app_settings: Settings):
        assert container is None or container.settings is app_settings
        return container or make_container(store_provider, app_settings)

    app = create_app(settings=settings, container_factory=factory, bootstrap_index=False)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client(container, settings):
    with make_client(settings, container=container) as test_client:
        yield test_client


CATALOG_CSV = (
    "Título Original,Ano de Lançamento,Direção / Um filme de / Uma obra de ,Sinopse,"
    "Descrição Completa,Palavras-Chave,Tags\n"
    'Lavra dor,1968,"Ana Carolina, Paulo Rufino",Sindicalismo rural,,"trabalhador rural, gado",\n'
    "Sensemayá,2021,Colectivo Los Ingrávidos,,Inspirado no poema,,\n"
    'Lavra dor,1968,"Ana Carolina; Paulo Rufino",Sindicalismo rural,,,\n'
    ",1999,Sem título,,,,\n"
)


@pytest.fixture
def catalog_csv(tmp_path):
    path = tmp_path / "catalog.csv"
    path.write_text(CATALOG_CSV, encoding="utf-8")
    return path
