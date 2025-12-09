from fastapi import APIRouter
from app.routers.health import router as health_router
from app.routers.search import router as search_router
from app.routers.index import router as index_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(search_router, prefix="/search", tags=["search"])
api_router.include_router(index_router, prefix="/index", tags=["indexing"])
