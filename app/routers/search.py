from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter()
search_service = SearchService()


@router.post(
    "/search/semantic",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Search",
    description="Perform semantic search on movie database using natural language queries",
)
async def semantic_search(request: SearchRequest) -> SearchResponse:
    """
    Endpoint for semantic search on movies.

    Args:
        request: Search request with query and parameters

    Returns:
        SearchResponse with matching movies ranked by similarity

    Raises:
        HTTPException: If search fails
    """
    try:
        result = await search_service.semantic_search(request)
        return result
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the search service is healthy",
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Dict with service status and document count
    """
    try:
        doc_count = search_service.weaviate_provider.count_documents()
        return {
            "status": "healthy",
            "service": "semantic_search",
            "indexed_documents": doc_count,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unhealthy"
        )
