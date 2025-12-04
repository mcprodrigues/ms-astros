from functools import lru_cache
import logging
from fastapi.params import Depends
from typing_extensions import Annotated

from app.providers.pipelines.semantic_search import SearchPipeline, get_search_pipeline
from app.schemas.movie import MovieResponse
from app.schemas.search import SearchRequest, SearchResponse
from app.services.interfaces import ISearchService

logger = logging.getLogger(__name__)


class SearchService(ISearchService):
    """
    Service responsible only for semantic search operations.
    """

    def __init__(self, search_pipeline: SearchPipeline = None):
        self.search_pipeline = search_pipeline or SearchPipeline()

    async def semantic_search(self, search_request: SearchRequest) -> SearchResponse:
        try:
            logger.info(f"Executing semantic search: {search_request.query}")

            documents = self.search_pipeline.search(
                query=search_request.query,
                top_k=search_request.top_k,
            )

            results = []

            for doc in documents:
                score = getattr(doc, "score", 1.0)

                if score >= search_request.min_score:
                    results.append(
                        MovieResponse(
                            titulo=doc.meta.get("titulo", ""),
                            sinopse=doc.meta.get("sinopse", ""),
                            descricao=doc.meta.get("descricao", ""),
                            palavras_chave=doc.meta.get("palavras_chave", ""),
                            diretor=doc.meta.get("diretor", ""),
                            score=round(score, 4),
                        )
                    )

            return SearchResponse(
                query=search_request.query,
                total_results=len(results),
                results=results,
            )

        except Exception as e:
            logger.error(f"Search error: {e}")
            raise


@lru_cache()
def get_search_service(
    pipeline: Annotated[SearchPipeline, Depends(get_search_pipeline)],
) -> ISearchService:
    return SearchService(search_pipeline=pipeline)
