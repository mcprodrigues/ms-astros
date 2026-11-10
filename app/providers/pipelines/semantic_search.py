import logging

from haystack import Document, Pipeline

from app.providers.pipelines.interfaces import (
    IDocumentStoreProvider,
    IRetrieverFactory,
    ISearchPipeline,
)

logger = logging.getLogger(__name__)


class SearchPipeline(ISearchPipeline):
    """Query-time retrieval over the document store."""

    def __init__(
        self,
        document_store_provider: IDocumentStoreProvider,
        retriever_factory: IRetrieverFactory,
    ):
        self.document_store_provider = document_store_provider
        self.retriever_factory = retriever_factory
        self.pipeline = self._build_pipeline()

    def search(self, query: str, top_k: int = 10) -> list[Document]:
        result = self.pipeline.run({"retriever": {"query": query, "top_k": top_k}})
        documents = result["retriever"]["documents"]
        logger.info("Search returned %d documents", len(documents))
        return documents

    def _build_pipeline(self) -> Pipeline:
        pipeline = Pipeline()
        store = self.document_store_provider.get_document_store()
        pipeline.add_component("retriever", self.retriever_factory.create_retriever(store))
        return pipeline
