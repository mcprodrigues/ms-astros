import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_indexing_service
from app.services.interfaces import IIndexingService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Returns 200 when the index backend is reachable, 503 otherwise.",
)
async def health_check(
    service: IIndexingService = Depends(get_indexing_service),
) -> dict[str, Any]:
    if not await service.is_ready():
        logger.error("Readiness check failed: index backend unreachable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Index backend unavailable"
        )
    count = await service.get_document_count()
    return {"status": "healthy", "indexed_documents": count["document_count"]}
