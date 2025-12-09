import logging
from haystack_integrations.components.retrievers.weaviate import WeaviateBM25Retriever
from haystack_integrations.document_stores.weaviate import WeaviateDocumentStore

logger = logging.getLogger(__name__)


class RetrieverComponent:
    """
    Retriever component factory.
    Creates and configures Weaviate BM25 retriever instances.
    """

    @staticmethod
    def create_retriever(
        document_store: WeaviateDocumentStore,
    ) -> WeaviateBM25Retriever:
        """
        Create a BM25 retriever instance.

        Args:
            document_store: WeaviateDocumentStore instance

        Returns:
            WeaviateBM25Retriever: Configured retriever component
        """
        try:
            retriever = WeaviateBM25Retriever(document_store=document_store)
            logger.info("Weaviate BM25 retriever created successfully")
            return retriever
        except Exception as e:
            logger.error(f"Failed to create retriever: {e}")
            raise
