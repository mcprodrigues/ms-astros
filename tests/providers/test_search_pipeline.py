import pytest

from app.providers.pipelines.components.retriever import RetrieverComponent


@pytest.fixture
def indexed(container):
    container.indexing_pipeline.index_batch_documents(
        [
            {"doc_id": "lavra", "content": "sindicalismo rural", "metadata": {}},
            {"doc_id": "sense", "content": "férias de família no méxico", "metadata": {}},
        ]
    )
    return container


def test_search_matches_by_meaning_without_shared_words(indexed):
    results = indexed.search_pipeline.search("luta no campo", top_k=1)

    assert [doc.id for doc in results] == ["lavra"]


def test_search_scores_are_cosine_similarity_best_first(indexed):
    results = indexed.search_pipeline.search("sindicalismo rural", top_k=2)

    assert [doc.id for doc in results] == ["lavra", "sense"]
    assert results[0].score == pytest.approx(1.0, abs=1e-3)
    assert results[1].score < 0.1


@pytest.mark.parametrize(("certainty", "cosine"), [(1.0, 1.0), (0.5, 0.0), (0.0, -1.0)])
def test_weaviate_certainty_is_converted_to_cosine(certainty, cosine):
    assert RetrieverComponent().to_cosine_similarity(certainty) == pytest.approx(cosine)
