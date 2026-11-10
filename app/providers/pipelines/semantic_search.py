import logging
from dataclasses import replace

from haystack import Document, Pipeline

from app.providers.pipelines.interfaces import (
    IDocumentStoreProvider,
    IEmbedder,
    IRetrieverFactory,
    ISearchPipeline,
)

logger = logging.getLogger(__name__)


class SearchPipeline(ISearchPipeline):
    """Embeds the query with the same model used at indexing time, then runs vector search."""

    def __init__(
        self,
        document_store_provider: IDocumentStoreProvider,
        embedder: IEmbedder,
        retriever_factory: IRetrieverFactory,
    ):
        self.document_store_provider = document_store_provider
        self.embedder = embedder
        self.retriever_factory = retriever_factory
        self.pipeline = self._build_pipeline()

    def search(self, query: str, top_k: int = 10) -> list[Document]:
        query_embedding = self.embedder.encode(query).tolist()
        result = self.pipeline.run(
            {"retriever": {"query_embedding": query_embedding, "top_k": top_k}}
        )
        documents = [
            replace(doc, score=self.retriever_factory.to_cosine_similarity(doc.score))
            for doc in result["retriever"]["documents"]
        ]
        logger.info("Search returned %d documents", len(documents))
        return documents

    def _build_pipeline(self) -> Pipeline:
        pipeline = Pipeline()
        store = self.document_store_provider.get_document_store()
        pipeline.add_component("retriever", self.retriever_factory.create_retriever(store))
        return pipeline
