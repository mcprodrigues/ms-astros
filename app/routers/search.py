from fastapi import APIRouter, Depends, status

from app.dependencies import get_search_service
from app.schemas.search import SearchRequest, SearchResponse
from app.services.interfaces import ISearchService

router = APIRouter()


@router.post(
    "/semantic",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Search",
    description="Find movies by meaning using a natural language query",
)
async def semantic_search(
    request: SearchRequest,
    service: ISearchService = Depends(get_search_service),
) -> SearchResponse:
    return await service.semantic_search(request)
