import logging

from haystack_integrations.components.retrievers.weaviate import WeaviateEmbeddingRetriever
from haystack_integrations.document_stores.weaviate import WeaviateDocumentStore

from app.providers.pipelines.interfaces import IRetrieverFactory

logger = logging.getLogger(__name__)


class RetrieverComponent(IRetrieverFactory):
    """Creates Weaviate vector retrievers bound to a document store."""

    def create_retriever(self, document_store: WeaviateDocumentStore) -> WeaviateEmbeddingRetriever:
        retriever = WeaviateEmbeddingRetriever(document_store=document_store)
        logger.info("Weaviate embedding retriever created")
        return retriever

    def to_cosine_similarity(self, raw_score: float) -> float:
        # Weaviate reports `certainty` for vector search; with the cosine
        # distance metric certainty = (1 + cos) / 2, so cos = 2 * certainty - 1.
        return 2.0 * raw_score - 1.0
