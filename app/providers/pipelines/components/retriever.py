import logging

from haystack_integrations.components.retrievers.weaviate import WeaviateBM25Retriever
from haystack_integrations.document_stores.weaviate import WeaviateDocumentStore

from app.providers.pipelines.interfaces import IRetrieverFactory

logger = logging.getLogger(__name__)


class RetrieverComponent(IRetrieverFactory):
    """Creates Weaviate retrievers bound to a document store."""

    def create_retriever(self, document_store: WeaviateDocumentStore) -> WeaviateBM25Retriever:
        retriever = WeaviateBM25Retriever(document_store=document_store)
        logger.info("Weaviate BM25 retriever created")
        return retriever
