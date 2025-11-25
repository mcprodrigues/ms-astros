import logging
from typing import List
from haystack import Document, Pipeline

from app.providers.pipelines.components.retriever import RetrieverComponent
from app.providers.pipelines.components.store import DocumentStoreProvider


logger = logging.getLogger(__name__)


class SearchPipeline:
    """
    Search pipeline for semantic retrieval.
    Uses Haystack Pipeline to orchestrate BM25 search.
    """

    def __init__(self):
        self.document_store_provider = DocumentStoreProvider()
        self.pipeline = self._build_pipeline()

    def search(self, query: str, top_k: int = 10) -> List[Document]:
        """
        Execute semantic search using the pipeline.

        Args:
            query: Search query string
            top_k: Maximum number of results to return

        Returns:
            List[Document]: Retrieved documents with scores
        """
        try:
            result = self.pipeline.run({"retriever": {"query": query, "top_k": top_k}})

            documents = result["retriever"]["documents"]
            logger.info(f"Search returned {len(documents)} documents")
            return documents

        except Exception as e:
            logger.error(f"Error executing search: {e}")
            raise

    def _build_pipeline(self) -> Pipeline:
        """
        Build the search pipeline with BM25 retriever component.

        Returns:
            Pipeline: Configured search pipeline
        """
        pipeline = Pipeline()

        document_store = self.document_store_provider.get_document_store()
        retriever = RetrieverComponent.create_retriever(document_store)

        pipeline.add_component("retriever", retriever)

        logger.info("Search pipeline built successfully")
        return pipeline
