"""
Provider interfaces for embedding, retrieval, document store, indexing, and search pipelines.
Defines abstract base classes (ABCs) to enforce consistent implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np
from haystack import Document


class IEmbedder(ABC):
    """
    Interface for the embedding provider (EmbedderComponent).
    Defines the contract for generating vector embeddings.
    """

    @abstractmethod
    def encode(self, text: str) -> np.ndarray:
        """
        Generate an embedding for a single text input.
        """
        pass

    @abstractmethod
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts in a batch.
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Return the dimensionality of the embeddings produced by the model.
        """
        pass


class IRetrieverFactory(ABC):
    """
    Interface for a retriever factory.
    Responsible for creating retriever instances (e.g., BM25 retriever).
    """

    @abstractmethod
    def create_retriever(self, document_store: Any) -> Any:
        """
        Create and return a retriever configured for the given document store.
        """
        pass


class IDocumentStoreProvider(ABC):
    """
    Interface for the Document Store provider.
    Defines the contract for returning a configured document store instance.
    """

    @abstractmethod
    def get_document_store(self) -> Any:
        """
        Return the initialized document store instance.
        """
        pass


class IIndexingPipeline(ABC):
    """
    Interface for the indexing pipeline.
    Defines operations for document ingestion and management.
    """

    @abstractmethod
    def index_single_document(
        self, content: str, metadata: Dict[str, Any], doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Index a single document into the vector database.
        """
        pass

    @abstractmethod
    def index_batch_documents(
        self, documents_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Index multiple documents in batch.
        """
        pass

    @abstractmethod
    def count_documents(self) -> int:
        """
        Return the total number of documents stored.
        """
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """
        Remove a document by its ID.
        """
        pass

    @abstractmethod
    def reset_index(self) -> None:
        """
        Reset the entire index (dangerous operation).
        """
        pass


class ISearchPipeline(ABC):
    """
    Interface for the semantic search pipeline.
    """

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[Document]:
        """
        Perform a semantic search query and return retrieved documents.
        """
        pass
