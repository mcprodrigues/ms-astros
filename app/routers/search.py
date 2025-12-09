from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app.schemas.search import SearchRequest, SearchResponse
from app.services.interfaces import ISearchService
from app.services.search import get_search_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/semantic",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Search",
    description="Perform semantic search on movie database using natural language queries",
)
async def semantic_search(
    request: SearchRequest,
    service: ISearchService = Depends(get_search_service),
) -> SearchResponse:
    """
    Endpoint for semantic search on movies.

    Args:
        request: Search request with query and parameters

    Returns:
        SearchResponse with matching movies ranked by similarity
    """
    try:
        result = await service.semantic_search(request)
        return result
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )