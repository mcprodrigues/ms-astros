import pytest

from app.dependencies import ensure_index_matches_embedder
from app.domain.errors import EmbeddingModelMismatchError
from tests.fakes import DIM, FakeEmbedder, InMemoryStoreProvider, make_document


def test_empty_index_accepts_any_model():
    ensure_index_matches_embedder(InMemoryStoreProvider(), FakeEmbedder())


def test_index_with_same_dimension_is_accepted():
    provider = InMemoryStoreProvider()
    provider.store.write_documents([make_document("a", "A")])

    ensure_index_matches_embedder(provider, FakeEmbedder())


def test_index_with_other_dimension_is_refused():
    provider = InMemoryStoreProvider()
    doc = make_document("a", "A")
    doc.embedding = [0.1] * (DIM + 379)
    provider.store.write_documents([doc])

    with pytest.raises(EmbeddingModelMismatchError, match=f"384-dimensional.*produces {DIM}"):
        ensure_index_matches_embedder(provider, FakeEmbedder())
