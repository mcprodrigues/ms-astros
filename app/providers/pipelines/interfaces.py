"""
Contracts for pipeline components and pipelines.

Concrete classes implement these ABCs and receive their collaborators through
the constructor; wiring happens only in `app.dependencies`.
"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from haystack import Document


class IEmbedder(ABC):
    """Generates vector embeddings for text."""

    @abstractmethod
    def encode(self, text: str) -> np.ndarray:
        """Embed a single text."""

    @abstractmethod
    def encode_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Embed many texts; returns one row per input text."""

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Dimensionality of the vectors this model produces."""


class IDocumentStoreProvider(ABC):
    """Owns the connection to the document store."""

    @abstractmethod
    def get_document_store(self) -> Any:
        """Return the initialized document store."""

    @abstractmethod
    def is_ready(self) -> bool:
        """True when the backing store answers readiness checks."""

    @abstractmethod
    def wait_until_ready(self) -> None:
        """Block until the store is ready, retrying with backoff; raise if it never is."""

    @abstractmethod
    def close(self) -> None:
        """Release the connection."""


class IRetrieverFactory(ABC):
    """Builds retriever components bound to a document store."""

    @abstractmethod
    def create_retriever(self, document_store: Any) -> Any:
        """Create a retriever for the given document store."""


class IIndexingPipeline(ABC):
    """Document ingestion and index management."""

    @abstractmethod
    def index_single_document(
        self, content: str, metadata: dict[str, Any], doc_id: str | None = None
    ) -> dict[str, Any]:
        """Embed and index one document."""

    @abstractmethod
    def index_batch_documents(self, documents_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Embed and index many documents."""

    @abstractmethod
    def index_precomputed_documents(self, documents: list[Document]) -> int:
        """Index documents that already carry embeddings; returns how many were written."""

    @abstractmethod
    def count_documents(self) -> int:
        """Total number of indexed documents."""

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """Remove a document by ID."""

    @abstractmethod
    def reset_index(self) -> None:
        """Delete every document in the index (destructive)."""

    @abstractmethod
    def is_ready(self) -> bool:
        """True when the underlying store is reachable."""


class ISearchPipeline(ABC):
    """Query-time retrieval."""

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> list[Document]:
        """Return documents ranked by relevance to the query."""
