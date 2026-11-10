import pytest
from weaviate.classes.config import DataType, Property

from app.bootstrap import load_precomputed_embeddings_if_empty
from app.dependencies import build_document_store_provider
from app.domain.errors import StoreSchemaError
from app.domain.movie import make_movie_id
from app.scripts.save_embeddings import EmbeddingSaver
from tests.integration.conftest import API_KEY

pytestmark = pytest.mark.integration
AUTH = {"X-API-Key": API_KEY}
LAVRA_DOR = make_movie_id("Lavra dor", 1968)


def upload(client, path):
    return client.post(
        "/api/v1/index/batch/csv",
        files={"file": ("catalogo.csv", path.read_bytes(), "text/csv")},
        headers=AUTH,
    )


def test_collection_declares_id_as_text_not_auto_schema_uuid(empty_container):
    store = empty_container.document_store_provider.get_document_store()
    types = {p.name: p.data_type for p in store.collection.config.get().properties}

    assert types["_original_id"] == DataType.TEXT
    assert types["score"] == DataType.NUMBER


def test_uuid_shaped_ids_round_trip_as_strings(live_client, catalog_csv):
    upload(live_client, catalog_csv)

    response = live_client.post(
        "/api/v1/search/semantic", json={"query": "luta no campo", "min_score": 0}
    )

    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["results"]]
    assert LAVRA_DOR in ids


def test_upload_search_delete_reset_flow(live_client, catalog_csv):
    first = upload(live_client, catalog_csv).json()
    second = upload(live_client, catalog_csv).json()
    assert (first["inserted"], second["inserted"], second["updated"]) == (2, 0, 2)

    top = live_client.post(
        "/api/v1/search/semantic",
        json={"query": "reforma agrária e trabalhadores rurais", "top_k": 1, "min_score": 0},
    ).json()["results"][0]
    assert top["titulo"] == "Lavra dor"
    assert top["diretor"] == "Ana Carolina, Paulo Rufino"
    assert 0 < top["score"] <= 1

    assert live_client.delete(f"/api/v1/index/movie/{LAVRA_DOR}", headers=AUTH).status_code == 200
    assert live_client.delete(f"/api/v1/index/movie/{LAVRA_DOR}", headers=AUTH).status_code == 404

    assert live_client.post("/api/v1/index/reset", headers=AUTH).status_code == 200
    assert live_client.get("/api/v1/index/count").json()["document_count"] == 0


def test_readiness_against_live_store(live_client):
    assert live_client.get("/api/v1/health").status_code == 200


def test_bootstrap_from_parquet_is_idempotent(empty_container, catalog_csv, tmp_path):
    from app.domain.catalog_io import read_catalog_csv

    saver = EmbeddingSaver(embedder=empty_container.embedder, output_dir=tmp_path)
    path = saver.save_as_parquet(saver.generate_embeddings(read_catalog_csv(catalog_csv).movies))

    first = load_precomputed_embeddings_if_empty(
        empty_container.indexing_pipeline, empty_container.embedder, path
    )
    second = load_precomputed_embeddings_if_empty(
        empty_container.indexing_pipeline, empty_container.embedder, path
    )

    assert (first, second) == (2, 0)
    assert empty_container.indexing_pipeline.count_documents() == 2


def test_incompatible_existing_schema_is_refused(integration_settings, live_container):
    name = f"{integration_settings.WEAVIATE_INDEX_NAME}Bad"
    client = live_container.document_store_provider.get_document_store().client
    client.collections.create(
        name, properties=[Property(name="_original_id", data_type=DataType.UUID)]
    )
    provider = build_document_store_provider(
        integration_settings.model_copy(update={"WEAVIATE_INDEX_NAME": name})
    )
    try:
        with pytest.raises(StoreSchemaError, match="_original_id is uuid, expected text"):
            provider.ensure_compatible_schema()
    finally:
        client.collections.delete(name)
        provider.close()


def test_stored_vector_dimension_matches_live_model(live_client, empty_container, catalog_csv):
    provider = empty_container.document_store_provider
    assert provider.stored_vector_dimension() is None

    upload(live_client, catalog_csv)

    assert provider.stored_vector_dimension() == empty_container.embedder.get_embedding_dimension()
