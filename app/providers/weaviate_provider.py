import logging
from typing import List, Optional
from haystack import Document
from haystack_integrations.document_stores.weaviate import WeaviateDocumentStore
from haystack_integrations.components.retrievers.weaviate import WeaviateBM25Retriever
from haystack_integrations.components.retrievers.weaviate import (
    WeaviateEmbeddingRetriever,
)
import weaviate
from weaviate.classes.config import Configure, Property, DataType

from app.settings import settings

logger = logging.getLogger(__name__)


class WeaviateProvider:
    """
    Weaviate infrastructure provider.
    Manages connection to Weaviate and provides document store and retriever instances.
    Implements singleton pattern to ensure single connection instance.
    """

    _instance: Optional["WeaviateProvider"] = None
    _document_store: Optional[WeaviateDocumentStore] = None
    _retriever: Optional[WeaviateEmbeddingRetriever] = None

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super(WeaviateProvider, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Weaviate provider if not already initialized."""
        if self._document_store is None:
            self._initialize_connection()

    def _initialize_connection(self) -> None:
        """
        Initialize connection to Weaviate and create document store.
        Configures the index with appropriate vectorizer settings.
        """
        try:
            logger.info(f"Connecting to Weaviate at {settings.WEAVIATE_URL}")

            # Initialize document store with text2vec-transformers
            self._document_store = WeaviateDocumentStore(
                url=settings.WEAVIATE_URL,
                collection_settings={
                    "class": settings.WEAVIATE_INDEX_NAME,
                    "vectorizer": "text2vec-transformers",
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "indexSearchable": True,
                        },
                        {
                            "name": "titulo",
                            "dataType": ["text"],
                            "indexSearchable": True,
                        },
                        {
                            "name": "sinopse",
                            "dataType": ["text"],
                            "indexSearchable": True,
                        },
                        {
                            "name": "descricao",
                            "dataType": ["text"],
                            "indexSearchable": True,
                        },
                        {
                            "name": "palavras_chave",
                            "dataType": ["text"],
                            "indexSearchable": True,
                        },
                        {
                            "name": "diretor",
                            "dataType": ["text"],
                            "indexSearchable": True,
                        },
                    ],
                },
            )

            logger.info("Weaviate document store initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Weaviate connection: {e}")
            raise

    def get_document_store(self) -> WeaviateDocumentStore:
        """
        Get the Weaviate document store instance.

        Returns:
            WeaviateDocumentStore: The initialized document store
        """
        if self._document_store is None:
            self._initialize_connection()
        return self._document_store

    def get_retriever(self) -> WeaviateEmbeddingRetriever:
        """
        Get or create the Weaviate embedding retriever instance.

        Returns:
            WeaviateEmbeddingRetriever: The configured retriever
        """
        if self._retriever is None:
            document_store = self.get_document_store()
            self._retriever = WeaviateBM25Retriever(document_store=document_store)
            logger.info("Weaviate retriever initialized successfully")

        return self._retriever

    def write_documents(self, documents: List[Document]) -> int:
        """
        Write documents to Weaviate.

        Args:
            documents: List of Haystack Document objects to index

        Returns:
            int: Number of documents written
        """
        try:
            document_store = self.get_document_store()
            document_store.write_documents(documents)
            logger.info(f"Successfully wrote {len(documents)} documents to Weaviate")
            return len(documents)
        except Exception as e:
            logger.error(f"Error writing documents to Weaviate: {e}")
            raise

    def count_documents(self) -> int:
        """
        Count total documents in the index.

        Returns:
            int: Total number of documents
        """
        try:
            document_store = self.get_document_store()
            return document_store.count_documents()
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
