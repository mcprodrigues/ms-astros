from fastapi import APIRouter
from app.routers.search import router as search_router
from app.routers.index import router as index_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(search_router)
api_router.include_router(index_router)
