"""Test doubles implementing the production interfaces."""

from typing import Any

import numpy as np
from haystack import Document
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
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

DIM = 4


class FakeEmbedder(IEmbedder):
    def encode(self, text: str) -> np.ndarray:
        return np.full(DIM, float(len(text) % 7), dtype=np.float32)

    def encode_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        return np.stack([self.encode(t) for t in texts])

    def get_embedding_dimension(self) -> int:
        return DIM


class InMemoryStoreProvider(IDocumentStoreProvider):
    def __init__(self, ready: bool = True):
        self.store = InMemoryDocumentStore()
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


class InMemoryBM25RetrieverFactory(IRetrieverFactory):
    def create_retriever(self, document_store: Any) -> InMemoryBM25Retriever:
        return InMemoryBM25Retriever(document_store=document_store)


def make_container(store_provider: InMemoryStoreProvider | None = None) -> Container:
    provider = store_provider or InMemoryStoreProvider()
    embedder = FakeEmbedder()
    indexing = IndexingPipeline(document_store_provider=provider, embedder=embedder)
    search = SearchPipeline(
        document_store_provider=provider, retriever_factory=InMemoryBM25RetrieverFactory()
    )
    return Container(
        settings=Settings(),
        document_store_provider=provider,
        embedder=embedder,
        indexing_pipeline=indexing,
        search_pipeline=search,
        indexing_service=IndexingService(indexing_pipeline=indexing),
        search_service=SearchService(search_pipeline=search),
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
