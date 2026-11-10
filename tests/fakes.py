"""Test doubles implementing the production interfaces."""

from typing import Any

import numpy as np
from haystack import Document
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore

from app.dependencies import Container
from app.providers.pipelines.indexing import IndexingPipeline
from app.providers.pipelines.interfaces import (
    IDocumentStoreProvider,
    IEmbedder,
    IRetrieverFactory,
)
from app.providers.pipelines.semantic_search import SearchPipeline
from app.services.indexing import IndexingService
from app.services.search import SearchService
from app.settings import Settings

# Words mapped onto "concept" axes, so related words share a direction even
# with no lexical overlap ("campo" ~ "rural"). The last axis is a small bias
# that keeps every vector non-zero.
CONCEPTS = {
    "rural": 0,
    "campo": 0,
    "terra": 0,
    "sindicalismo": 1,
    "luta": 1,
    "trabalho": 1,
    "férias": 2,
    "família": 2,
    "infância": 2,
    "méxico": 3,
    "poema": 3,
}
DIM = 5


class FakeEmbedder(IEmbedder):
    model_name = "fake-concept-model"

    def encode(self, text: str) -> np.ndarray:
        vector = np.zeros(DIM, dtype=np.float32)
        vector[-1] = 0.01
        for word in text.lower().replace(".", " ").replace(",", " ").split():
            if word in CONCEPTS:
                vector[CONCEPTS[word]] += 1.0
        return vector

    def encode_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        return np.stack([self.encode(t) for t in texts])

    def get_embedding_dimension(self) -> int:
        return DIM


class InMemoryStoreProvider(IDocumentStoreProvider):
    def __init__(self, ready: bool = True):
        self.store = InMemoryDocumentStore(embedding_similarity_function="cosine")
        self.ready = ready
        self.closed = False

    def get_document_store(self) -> InMemoryDocumentStore:
        return self.store

    def is_ready(self) -> bool:
        return self.ready

    def wait_until_ready(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class InMemoryEmbeddingRetrieverFactory(IRetrieverFactory):
    """In-memory cosine retrieval: native score already is cosine similarity."""

    def create_retriever(self, document_store: Any) -> InMemoryEmbeddingRetriever:
        return InMemoryEmbeddingRetriever(document_store=document_store)

    def to_cosine_similarity(self, raw_score: float) -> float:
        return raw_score


def make_container(store_provider: InMemoryStoreProvider | None = None) -> Container:
    provider = store_provider or InMemoryStoreProvider()
    embedder = FakeEmbedder()
    indexing = IndexingPipeline(document_store_provider=provider, embedder=embedder)
    search = SearchPipeline(
        document_store_provider=provider,
        embedder=embedder,
        retriever_factory=InMemoryEmbeddingRetrieverFactory(),
    )
    return Container(
        settings=Settings(),
        document_store_provider=provider,
        embedder=embedder,
        indexing_pipeline=indexing,
        search_pipeline=search,
        indexing_service=IndexingService(indexing_pipeline=indexing),
        search_service=SearchService(
            search_pipeline=search, default_top_k=5, default_min_score=0.5
        ),
    )


def make_document(doc_id: str, titulo: str) -> Document:
    return Document(
        id=doc_id,
        content=titulo,
        embedding=[0.1] * DIM,
        meta={
            "titulo": titulo,
            "sinopse": "",
            "descricao": "",
            "palavras_chave": "",
            "diretor": "",
        },
    )
