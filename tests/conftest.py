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
