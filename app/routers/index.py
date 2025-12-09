"""
Index router for incremental document ingestion.
Provides endpoints for single uploads, batch operations, and management.
"""

import logging
from fastapi import APIRouter, HTTPException, Form, Depends
from typing import Optional

from app.schemas.movie import MovieUpload
from app.services.indexing import get_indexing_service
from app.services.interfaces import IIndexingService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/movie")
async def ingest_single_movie(
    movie: MovieUpload,
    service: IIndexingService = Depends(get_indexing_service),
):
    """
    Ingest a single movie document incrementally.
    """
    try:
        return await service.ingest_single_movie(
            titulo=movie.titulo,
            sinopse=movie.sinopse,
            descricao=movie.descricao,
            palavras_chave=movie.palavras_chave,
            diretor=movie.diretor,
            movie_id=movie.movie_id,
        )
    except Exception as e:
        logger.error(f"Single movie ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/movie/form")
async def ingest_movie_form(
    service: IIndexingService = Depends(get_indexing_service),
    titulo: str = Form(...),
    sinopse: str = Form(""),
    descricao: str = Form(""),
    palavras_chave: str = Form(""),
    diretor: str = Form(""),
    movie_id: Optional[str] = Form(None),
):
    """
    Ingest a single movie via HTML form or multipart/form-data.
    """
    try:
        return await service.ingest_single_movie(
            titulo=titulo,
            sinopse=sinopse,
            descricao=descricao,
            palavras_chave=palavras_chave,
            diretor=diretor,
            movie_id=movie_id,
        )
    except Exception as e:
        logger.error(f"Form movie ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/csv")
async def ingest_batch_from_csv(
    service: IIndexingService = Depends(get_indexing_service),
    csv_path: str = "data/movies.csv",
):
    """
    Ingest multiple movies in batch from CSV file.
    """
    try:
        return await service.ingest_movies_from_csv(csv_path)
    except Exception as e:
        logger.error(f"Batch CSV ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/movie/{movie_id}")
async def delete_movie(
    movie_id: str,
    service: IIndexingService = Depends(get_indexing_service),
):
    """
    Delete a movie document by ID.
    """
    try:
        return await service.delete_movie(movie_id)
    except Exception as e:
        logger.error(f"Delete movie error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/count")
async def get_document_count(
    service: IIndexingService = Depends(get_indexing_service),
):
    """
    Get total count of indexed documents.
    """
    try:
        return await service.get_document_count()
    except Exception as e:
        logger.error(f"Get count error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_index(
    service: IIndexingService = Depends(get_indexing_service),
):
    """
    Reset the entire index (dangerous).
    """
    try:
        service.indexing_pipeline.reset_index()

        return {
            "status": "success",
            "message": "Index reset complete. All documents deleted.",
        }
    except Exception as e:
        logger.error(f"Reset index error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
