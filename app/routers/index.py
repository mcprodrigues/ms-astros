from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter()
search_service = SearchService()


@router.post(
    "/index/movies",
    status_code=status.HTTP_200_OK,
    summary="Index Movies",
    description="Manually trigger movie indexation from CSV",
)
async def index_movies() -> Dict[str, Any]:
    """
    Manual indexation endpoint (optional, as indexation happens on startup).

    Returns:
        Dict with indexation results
    """
    try:
        result = await search_service.index_movies_from_csv()
        return result
    except Exception as e:
        logger.error(f"Indexation endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexation failed: {str(e)}",
        )
