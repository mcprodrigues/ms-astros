from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging

from app.services.indexing import get_indexing_service
from app.services.interfaces import IIndexingService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the search service is healthy",
)
async def health_check(
    service: IIndexingService = Depends(get_indexing_service),
) -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        doc_count = await service.get_document_count()
        return {
            "status": "healthy",
            "service": "semantic_search",
            "indexed_documents": doc_count,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )