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

    model_name: str

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
    def reset(self) -> None:
        """Delete every document, leaving an empty index with the declared schema."""

    @abstractmethod
    def ensure_compatible_schema(self) -> None:
        """Raise StoreSchemaError if an existing index has an incompatible schema."""

    @abstractmethod
    def document_exists(self, doc_id: str) -> bool:
        """True when a document with this ID is stored."""

    @abstractmethod
    def wait_until_ready(self) -> None:
        """Block until the store is ready, retrying with backoff; raise if it never is."""

    @abstractmethod
    def close(self) -> None:
        """Release the connection."""


class IRetrieverFactory(ABC):
    """Builds embedding retrievers bound to a document store."""

    @abstractmethod
    def create_retriever(self, document_store: Any) -> Any:
        """Create a retriever whose `run` accepts `query_embedding` and `top_k`."""

    @abstractmethod
    def to_cosine_similarity(self, raw_score: float) -> float:
        """Convert the backend's native score into cosine similarity."""


class IIndexingPipeline(ABC):
    """
    Document ingestion and index management.

    Implementations raise StoreUnavailableError when the store cannot be reached.
    """

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
        """Remove a document by ID; False when no such document exists."""

    @abstractmethod
    def reset_index(self) -> None:
        """Delete every document in the index (destructive)."""

    @abstractmethod
    def is_ready(self) -> bool:
        """True when the underlying store is reachable."""


class ISearchPipeline(ABC):
    """Query-time semantic retrieval."""

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> list[Document]:
        """
        Return the `top_k` documents most similar to the query, best first.

        Contract: each document's `score` is the cosine similarity between the
        query and document embeddings, whatever the backend.
        """
