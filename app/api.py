from fastapi import APIRouter


api_router = APIRouter(
    prefix="/api",
)

from app.routers.search import router as search_router

api_router.include_router(search_router)
