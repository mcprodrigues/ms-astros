"""
Indexing pipeline for incremental document ingestion.
Supports single document and batch uploads with embedding generation.
"""

from functools import lru_cache
import logging
from typing import Dict, List, Optional
from haystack import Document, Pipeline
from haystack.components.writers import DocumentWriter

from app.providers.pipelines.components.embedder import EmbedderComponent
from app.providers.pipelines.components.store import DocumentStoreProvider

logger = logging.getLogger(__name__)


class IndexingPipeline:
    """
    Indexing pipeline for incremental document ingestion.
    Generates embedding on-the-fly and indexes documents.
    """

    def __init__(self):
        self.document_store_provider = DocumentStoreProvider()
        self.embedder = EmbedderComponent()
        self.pipeline = self._build_pipeline()

    def index_single_document(
        self, content: str, metadata: Dict[str, any], doc_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Index a single document with embedding generation.
        Use case: Uploading a single document via API.

        Args:
            content: Document text content
            metadata: Document metadata
            doc_id: Optional document ID (auto-generated if not provided)

        Returns:
            Dict with indexing status and document info
        """

        try:
            logger.info(f"Indexing single document: {doc_id or 'auto-generated ID'} ")

            # Generate embedding
            embedding = self.embedder.encode(content)

            # Create Haystack Document
            document = Document(
                id=doc_id, content=content, embedding=embedding.tolist(), meta=metadata
            )

            # Index document
            result = self.pipeline.run({"writer": {"documents": [document]}})
            indexed_count = result["writer"]["documents_written"]

            logger.info(
                f"Document indexed successfully: {doc_id or 'auto-generated ID'}"
            )

            return {
                "status": "success",
                "document_id": doc_id,
                "indexed": indexed_count > 0,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Error indexing single document: {e}")
            raise

    def index_batch_documents(
        self, documents_data: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """
        Index multiple documents in batch with embedding generation.
        Use case: Uploading multiple documents via API.

        Args:
            documents_data: List of dicts with 'content', 'metadata', and optional 'doc_id'

        Returns:
            Dict with batch indexing status
        """

        try:
            logger.info(f"Starting batch indexing of {len(documents_data)} documents")

            # Extract texts for batch embedding
            texts = [doc_data["content"] for doc_data in documents_data]

            # Generate embeddings in batch (i think it's more efficient :p)
            embeddings = self.embedder.encode_batch(texts)

            # Create Haystack Documents
            documents = []
            for i, doc_data in enumerate(documents_data):
                document = Document(
                    id=doc_data.get("doc_id"),
                    content=doc_data["content"],
                    embedding=embeddings[i].tolist(),
                    meta=doc_data["metadata"],
                )
                documents.append(document)

            # Index documents
            result = self.pipeline.run({"writer": {"documents": documents}})
            indexed_count = result["writer"]["documents_written"]

            logger.info(
                f"Batch indexing complete: {indexed_count}/{len(documents_data)} documents indexed"
            )

            return {
                "status": "success",
                "indexed_count": indexed_count,
                "total_documents": len(documents_data),
                "failed_documents": len(documents_data) - indexed_count,
            }

        except Exception as e:
            logger.error(f"Error batch indexing documents: {e}")
            raise

    def count_documents(self) -> int:
        """
        Count total documents in the document store.

        Returns:
            int: Total document count
        """
        try:
            document_store = self.document_store_provider.get_document_store()
            count = document_store.count_documents()
            logger.info(f"Document store contains {count} documents")
            return count
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            document_store = self.document_store_provider.get_document_store()
            document_store.delete_documents([doc_id])
            logger.info(f"Document deleted: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False

    def reset_index(self) -> None:
        """
        Reset the entire index (dangerous operation).
        Clears all documents and recreates the collection.
        """
        try:
            logger.warning("Resetting entire index...")
            self.document_store_provider.reset_collection()
            self.pipeline = self._build_pipeline()
            logger.info("Index reset complete")
        except Exception as e:
            logger.error(f"Error resetting index: {e}")
            raise

    def _build_pipeline(self) -> Pipeline:
        """
        Build the indexing pipeline with DocumentWriter component.

        Returns:
            Pipeline: Configured indexing pipeline
        """
        pipeline = Pipeline()

        document_store = self.document_store_provider.get_document_store()
        writer = DocumentWriter(
            document_store=document_store,
            policy="overwrite",
        )

        pipeline.add_component("writer", writer)

        logger.info("Indexing pipeline built successfully")
        return pipeline


@lru_cache()
def get_indexing_pipeline() -> IndexingPipeline:
    """
    Get a cached instance of the IndexingPipeline.

    Returns:
        IndexingPipeline: Singleton indexing pipeline instance
    """
    return IndexingPipeline()