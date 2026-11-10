"""
Composition root: the only place concrete classes are instantiated and wired.

`build_container` is called once per process (in the FastAPI lifespan or by an
offline script). Request handlers read collaborators from `app.state.container`
through the `get_*` functions below, used with FastAPI `Depends`.
"""

from dataclasses import dataclass

from fastapi import Request

from app.domain.errors import EmbeddingModelMismatchError
from app.providers.pipelines.components.embedder import EmbedderComponent
from app.providers.pipelines.components.retriever import RetrieverComponent
from app.providers.pipelines.components.store import DocumentStoreProvider
from app.providers.pipelines.indexing import IndexingPipeline
from app.providers.pipelines.interfaces import (
    IDocumentStoreProvider,
    IEmbedder,
    IIndexingPipeline,
    ISearchPipeline,
)
from app.providers.pipelines.semantic_search import SearchPipeline
from app.services.indexing import IndexingService
from app.services.interfaces import IIndexingService, ISearchService
from app.services.search import SearchService
from app.settings import Settings


@dataclass(frozen=True)
class Container:
    settings: Settings
    document_store_provider: IDocumentStoreProvider
    embedder: IEmbedder
    indexing_pipeline: IIndexingPipeline
    search_pipeline: ISearchPipeline
    indexing_service: IIndexingService
    search_service: ISearchService

    def close(self) -> None:
        self.document_store_provider.close()


def build_document_store_provider(settings: Settings) -> IDocumentStoreProvider:
    return DocumentStoreProvider(
        url=settings.WEAVIATE_URL,
        index_name=settings.WEAVIATE_INDEX_NAME,
        grpc_port=settings.WEAVIATE_GRPC_PORT,
        connect_attempts=settings.WEAVIATE_CONNECT_ATTEMPTS,
        backoff_seconds=settings.WEAVIATE_CONNECT_BACKOFF_SECONDS,
        query_timeout_seconds=settings.WEAVIATE_QUERY_TIMEOUT_SECONDS,
        insert_timeout_seconds=settings.WEAVIATE_INSERT_TIMEOUT_SECONDS,
    )


def build_embedder(settings: Settings) -> IEmbedder:
    return EmbedderComponent(
        model_name=settings.EMBEDDING_MODEL,
        max_seq_length=settings.EMBEDDING_MAX_SEQ_LENGTH,
        revision=settings.EMBEDDING_MODEL_REVISION,
    )


def ensure_index_matches_embedder(
    store_provider: IDocumentStoreProvider, embedder: IEmbedder
) -> None:
    """
    Refuse to serve an index whose vectors came from a model with another
    dimension: every query would be rejected by the store.
    """
    stored = store_provider.stored_vector_dimension()
    expected = embedder.get_embedding_dimension()
    if stored is not None and stored != expected:
        raise EmbeddingModelMismatchError(
            f"The index holds {stored}-dimensional vectors but {embedder.model_name} "
            f"produces {expected}. Reset the index (POST /api/v1/index/reset, or drop the "
            "collection) and restart to reseed it from the precomputed embeddings."
        )


def build_container(settings: Settings) -> Container:
    """Wire the full object graph. Blocks until the document store is ready."""
    store_provider = build_document_store_provider(settings)
    store_provider.wait_until_ready()
    store_provider.ensure_compatible_schema()

    embedder = build_embedder(settings)
    ensure_index_matches_embedder(store_provider, embedder)
    indexing_pipeline = IndexingPipeline(document_store_provider=store_provider, embedder=embedder)
    search_pipeline = SearchPipeline(
        document_store_provider=store_provider,
        embedder=embedder,
        retriever_factory=RetrieverComponent(),
    )
    return Container(
        settings=settings,
        document_store_provider=store_provider,
        embedder=embedder,
        indexing_pipeline=indexing_pipeline,
        search_pipeline=search_pipeline,
        indexing_service=IndexingService(indexing_pipeline=indexing_pipeline),
        search_service=SearchService(
            search_pipeline=search_pipeline,
            default_top_k=settings.DEFAULT_TOP_K,
            default_min_score=settings.MIN_SCORE_THRESHOLD,
        ),
    )


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_settings(request: Request) -> Settings:
    return get_container(request).settings


def get_indexing_service(request: Request) -> IIndexingService:
    return get_container(request).indexing_service


def get_search_service(request: Request) -> ISearchService:
    return get_container(request).search_service
