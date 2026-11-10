import asyncio
import logging

from app.providers.pipelines.interfaces import ISearchPipeline
from app.schemas.movie import MovieResponse
from app.schemas.search import SearchRequest, SearchResponse
from app.services.interfaces import ISearchService

logger = logging.getLogger(__name__)


class SearchService(ISearchService):
    """Semantic search: retrieves, filters by similarity threshold, maps to the API schema."""

    def __init__(
        self,
        search_pipeline: ISearchPipeline,
        default_top_k: int = 5,
        default_min_score: float = 0.5,
    ):
        self.search_pipeline = search_pipeline
        self.default_top_k = default_top_k
        self.default_min_score = default_min_score

    async def semantic_search(self, search_request: SearchRequest) -> SearchResponse:
        top_k = search_request.top_k or self.default_top_k
        min_score = (
            search_request.min_score
            if search_request.min_score is not None
            else self.default_min_score
        )

        documents = await asyncio.to_thread(
            self.search_pipeline.search, query=search_request.query, top_k=top_k
        )
        results = [
            MovieResponse(
                id=doc.id,
                titulo=doc.meta.get("titulo", ""),
                sinopse=doc.meta.get("sinopse", ""),
                descricao=doc.meta.get("descricao", ""),
                palavras_chave=doc.meta.get("palavras_chave", ""),
                diretor=doc.meta.get("diretor", ""),
                score=round(doc.score, 4),
            )
            for doc in documents
            if doc.score is not None and doc.score >= min_score
        ]
        return SearchResponse(
            query=search_request.query, total_results=len(results), results=results
        )
