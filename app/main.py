import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routers.search import router as search_router
from app.routers.index import router as index_router
from app.services.search_service import SearchService


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown events.
    Handles the initialization of the search service and data indexing.
    """
    logger.info("Starting Astros Semantic Search API...")

    # Initialize search service and index data
    search_service = SearchService()

    try:
        # Wait for Weaviate to be ready
        await asyncio.sleep(10)

        # Index movies on startup
        logger.info("Starting movie indexation...")
        result = await search_service.index_movies_from_csv()
        logger.info(f"Indexation completed: {result}")

    except Exception as e:
        logger.error(f"Error during startup indexation: {e}")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down Astros Semantic Search API...")


# Initialize FastAPI application
app = FastAPI(
    title="Astros Semantic Search API",
    description="Semantic search microservice for cinema educational materials",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router, prefix="/api/v1", tags=["search"])
app.include_router(index_router, prefix="/api/v1", tags=["index"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Astros Semantic Search API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "semantic_search": "/api/v1/search/semantic",
            "health": "/api/v1/health",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
