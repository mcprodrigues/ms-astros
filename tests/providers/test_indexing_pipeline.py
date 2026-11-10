from tests.fakes import DIM, make_document


def test_index_single_document_returns_generated_id(container):
    result = container.indexing_pipeline.index_single_document(
        content="Lavra dor", metadata={"titulo": "Lavra dor"}
    )

    assert result["indexed"] is True
    assert result["document_id"]  # id is reported even when caller passed none
    assert container.indexing_pipeline.count_documents() == 1


def test_index_single_document_overwrites_same_id(container):
    pipeline = container.indexing_pipeline
    pipeline.index_single_document(content="v1", metadata={}, doc_id="m1")
    pipeline.index_single_document(content="v2", metadata={}, doc_id="m1")

    assert pipeline.count_documents() == 1


def test_index_batch_documents_embeds_every_document(container, store_provider):
    result = container.indexing_pipeline.index_batch_documents(
        [
            {"doc_id": "a", "content": "Lavra dor", "metadata": {}},
            {"doc_id": "b", "content": "Sensemayá", "metadata": {}},
        ]
    )

    assert result["indexed_count"] == 2
    assert result["failed_documents"] == 0
    stored = store_provider.store.filter_documents()
    assert all(doc.embedding is not None for doc in stored)


def test_index_precomputed_documents_keeps_given_embeddings(container, store_provider):
    written = container.indexing_pipeline.index_precomputed_documents(
        [make_document("a", "Lavra dor")]
    )

    assert written == 1
    assert store_provider.store.filter_documents()[0].embedding == [0.1] * DIM


def test_reset_index_deletes_everything(container):
    container.indexing_pipeline.index_precomputed_documents(
        [make_document("a", "A"), make_document("b", "B")]
    )

    container.indexing_pipeline.reset_index()

    assert container.indexing_pipeline.count_documents() == 0


def test_is_ready_delegates_to_store_provider(container, store_provider):
    assert container.indexing_pipeline.is_ready() is True
    store_provider.ready = False
    assert container.indexing_pipeline.is_ready() is False
