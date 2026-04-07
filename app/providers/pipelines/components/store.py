import logging
from typing import Optional
from haystack_integrations.document_stores.weaviate import WeaviateDocumentStore

from app.settings import settings

logger = logging.getLogger(__name__)


class DocumentStoreProvider:
    """
    Document store provider implementing singleton pattern.
    Manages single instance of Weaviate document store connection.
    """

    _instance: Optional["DocumentStoreProvider"] = None
    _document_store: Optional[WeaviateDocumentStore] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DocumentStoreProvider, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._document_store is None:
            self._initialize_document_store()

    def _initialize_document_store(self) -> None:
        """
        Initialize Weaviate document store with collection settings.
        Configures schema with searchable text properties.
        """
        try:
            logger.info(f"Connecting to Weaviate at {settings.WEAVIATE_URL}")

            self._document_store = WeaviateDocumentStore(
                url=settings.WEAVIATE_URL,
                collection_settings={
                    "class": settings.WEAVIATE_INDEX_NAME,
                    "vectorizer": "none",
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
            logger.error(f"Failed to initialize Weaviate document store: {e}")
            raise

    def get_document_store(self) -> WeaviateDocumentStore:
        """
        Get the document store instance.

        Returns:
            WeaviateDocumentStore: Initialized document store
        """
        if self._document_store is None:
            self._initialize_document_store()
        return self._document_store
