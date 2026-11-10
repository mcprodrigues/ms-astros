"""Indexing pipeline: embeds documents and writes them to the document store."""

import logging
from typing import Any

from haystack import Document, Pipeline
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy

from app.providers.pipelines.interfaces import IDocumentStoreProvider, IEmbedder, IIndexingPipeline
from app.providers.pipelines.store_guard import call_store

logger = logging.getLogger(__name__)


class IndexingPipeline(IIndexingPipeline):
    def __init__(self, document_store_provider: IDocumentStoreProvider, embedder: IEmbedder):
        self.document_store_provider = document_store_provider
        self.embedder = embedder
        self.pipeline = self._build_pipeline()

    def index_single_document(
        self, content: str, metadata: dict[str, Any], doc_id: str | None = None
    ) -> dict[str, Any]:
        embedding = self.embedder.encode(content)
        document = Document(id=doc_id, content=content, embedding=embedding.tolist(), meta=metadata)
        written = self._write([document])
        return {
            "status": "success",
            "document_id": document.id,
            "indexed": written > 0,
            "metadata": metadata,
        }

    def index_batch_documents(self, documents_data: list[dict[str, Any]]) -> dict[str, Any]:
        logger.info("Batch indexing %d documents", len(documents_data))
        embeddings = self.embedder.encode_batch([d["content"] for d in documents_data])
        documents = [
            Document(
                id=data.get("doc_id"),
                content=data["content"],
                embedding=embedding.tolist(),
                meta=data["metadata"],
            )
            for data, embedding in zip(documents_data, embeddings, strict=True)
        ]
        written = self._write(documents)
        return {
            "status": "success",
            "indexed_count": written,
            "total_documents": len(documents_data),
            "failed_documents": len(documents_data) - written,
        }

    def index_precomputed_documents(self, documents: list[Document]) -> int:
        return self._write(documents)

    def count_documents(self) -> int:
        return self._guard(lambda: self._store().count_documents())

    def delete_document(self, doc_id: str) -> bool:
        def delete() -> bool:
            if not self.document_store_provider.document_exists(doc_id):
                return False
            self._store().delete_documents([doc_id])
            return True

        return self._guard(delete)

    def reset_index(self) -> None:
        logger.warning("Resetting entire index")
        self._guard(self.document_store_provider.reset)
        logger.info("Index reset complete")

    def is_ready(self) -> bool:
        return self.document_store_provider.is_ready()

    def _guard(self, operation):
        return call_store(self.document_store_provider, operation)

    def _store(self):
        return self.document_store_provider.get_document_store()

    def _write(self, documents: list[Document]) -> int:
        result = self._guard(lambda: self.pipeline.run({"writer": {"documents": documents}}))
        return result["writer"]["documents_written"]

    def _build_pipeline(self) -> Pipeline:
        pipeline = Pipeline()
        pipeline.add_component(
            "writer", DocumentWriter(document_store=self._store(), policy=DuplicatePolicy.OVERWRITE)
        )
        return pipeline
