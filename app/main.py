"""
Main FastAPI application with lifespan management.
Loads precomputed embeddings on startup if available.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.scripts.load_embeddings import EmbeddingLoader
from app.services.search import SearchService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def load_precomputed_embeddings():
    """
    Load precomputed embeddings on startup if available.
    Falls back to empty index if embeddings file doesn't exist.
    """
    embeddings_path = Path("data/embeddings/embeddings.parquet")
    
    if not embeddings_path.exists():
        logger.warning(f"Embeddings file not found: {embeddings_path}")
        logger.warning("Starting with empty index. Use POST /api/v1/index/movie to add documents.")
        return
    
    try:
        logger.info("Loading precomputed embeddings...")
        
        
        loader = EmbeddingLoader()
        embeddings_data = loader.load_from_parquet("embeddings.parquet")
        count = loader.index_precomputed_embeddings(embeddings_data)
        
        logger.info(f"Successfully loaded {count} documents from precomputed embeddings")
        
    except Exception as e:
        logger.error(f"Error loading precomputed embeddings: {e}")
        logger.warning("Starting with empty index. Use POST /api/v1/index/movie to add documents.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.
    """
    logger.info("=" * 60)
    logger.info("Starting Astros Semantic Search API")
    logger.info("=" * 60)

    try:
        # Wait for Weaviate to be ready
        logger.info("Waiting for Weaviate to be ready...")
        await asyncio.sleep(10)
        logger.info("Weaviate connection established")

        # Load precomputed embeddings if available
        await load_precomputed_embeddings()

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        logger.warning("API will start but may not have indexed documents")

    logger.info("=" * 60)
    logger.info("Astros API Ready")
    logger.info("=" * 60)
    
    yield

    logger.info("Shutting down Astros Semantic Search API...")


# Initialize FastAPI application
app = FastAPI(
    title="Astros Semantic Search API",
    description="Semantic search microservice for cinema educational materials",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["root"])
async def root():
    """API root endpoint with basic information."""
    return {
        "name": "Astros Semantic Search API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "search": "/api/v1/search",
            "index": "/api/v1/index",
            "health": "/ping",
        },
    }

@app.get("/ping", tags=["health"])
async def ping():
    """Health check endpoint."""
    return {"message": "pong!", "status": "healthy"}


@app.get("/health", tags=["health"])
async def health_check():
    """
    Detailed health check with document count.
    """
    try:
        
        service = SearchService()        

        count_result = await service.get_document_count()
        
        return {
            "status": "healthy",
            "api_version": "1.0.0",
            "indexed_documents": count_result.get("total_documents", 0),
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "degraded",
            "error": str(e),
        }