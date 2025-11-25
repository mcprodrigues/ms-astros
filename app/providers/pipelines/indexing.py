import logging
from typing import List
from haystack import Document, Pipeline
from haystack.components.writers import DocumentWriter

from app.providers.pipelines.components.store import DocumentStoreProvider

logger = logging.getLogger(__name__)


class IndexingPipeline:
    """
    Indexing pipeline for writing documents to document store.
    Uses Haystack Pipeline to orchestrate document writing.
    """

    def __init__(self):
        self.document_store_provider = DocumentStoreProvider()
        self.pipeline = self._build_pipeline()

    def index_documents(self, documents: List[Document]) -> int:
        """
        Index documents using the pipeline.

        Args:
            documents: List of Haystack Document objects

        Returns:
            int: Number of documents indexed
        """
        try:
            result = self.pipeline.run({"writer": {"documents": documents}})
            indexed_count = result["writer"]["documents_written"]
            logger.info(f"Successfully indexed {indexed_count} documents")
            return indexed_count
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            raise

    def count_documents(self) -> int:
        """
        Count documents in the document store.

        Returns:
            int: Total document count
        """
        try:
            document_store = self.document_store_provider.get_document_store()
            return document_store.count_documents()
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0

    def _build_pipeline(self) -> Pipeline:
        """
        Build the indexing pipeline with DocumentWriter component.

        Returns:
            Pipeline: Configured indexing pipeline
        """
        pipeline = Pipeline()

        document_store = self.document_store_provider.get_document_store()
        writer = DocumentWriter(document_store=document_store)

        pipeline.add_component("writer", writer)

        logger.info("Indexing pipeline built successfully")
        return pipeline
