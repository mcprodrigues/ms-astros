"""FastAPI application factory and lifespan."""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.bootstrap import load_precomputed_embeddings_if_empty
from app.dependencies import Container, build_container
from app.error_handlers import register_error_handlers
from app.settings import Settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

API_VERSION = "1.0.0"


def create_app(
    settings: Settings | None = None,
    container_factory: Callable[[Settings], Container] = build_container,
    bootstrap_index: bool = True,
) -> FastAPI:
    """
    Build the application. Tests pass a `container_factory` returning fakes and
    `bootstrap_index=False` so no real Weaviate or model is needed.
    """
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Starting Astros API")
        container = await asyncio.to_thread(container_factory, settings)
        app.state.container = container
        if bootstrap_index:
            await asyncio.to_thread(
                load_precomputed_embeddings_if_empty,
                container.indexing_pipeline,
                container.embedder,
                Path(settings.EMBEDDINGS_PATH),
            )
        logger.info("Astros API ready")
        try:
            yield
        finally:
            logger.info("Shutting down Astros API")
            container.close()

    app = FastAPI(
        title="Astros Semantic Search API",
        description="Semantic search microservice for cinema educational materials",
        version=API_VERSION,
        lifespan=lifespan,
    )
    if settings.CORS_ALLOW_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOW_ORIGINS,
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Content-Type", "X-API-Key"],
        )
    register_error_handlers(app)
    app.include_router(api_router)

    @app.get("/", tags=["root"])
    async def root():
        return {
            "name": "Astros Semantic Search API",
            "version": API_VERSION,
            "endpoints": {
                "docs": "/docs",
                "search": "/api/v1/search",
                "index": "/api/v1/index",
                "liveness": "/ping",
                "readiness": "/api/v1/health",
            },
        }

    @app.get("/ping", tags=["health"])
    async def ping():
        """Liveness: the process is up. Does not touch dependencies."""
        return {"message": "pong!", "status": "alive"}

    return app


app = create_app()
