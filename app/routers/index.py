"""Index management: ingestion, deletion, counting, reset."""

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.dependencies import get_indexing_service, get_settings
from app.schemas.movie import MovieUpload
from app.security import require_api_key
from app.services.interfaces import IIndexingService
from app.settings import Settings

router = APIRouter()

CSV_CONTENT_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"}


@router.post("/movie", dependencies=[Depends(require_api_key)])
async def ingest_single_movie(
    movie: MovieUpload,
    service: IIndexingService = Depends(get_indexing_service),
) -> dict[str, Any]:
    """Ingest (or overwrite) a single movie."""
    return await service.ingest_single_movie(
        titulo=movie.titulo,
        sinopse=movie.sinopse,
        descricao=movie.descricao,
        palavras_chave=movie.palavras_chave,
        diretor=movie.diretor,
        movie_id=movie.movie_id,
        ano=movie.ano,
        tema=movie.tema,
        tags=movie.tags,
    )


@router.post("/movie/form", dependencies=[Depends(require_api_key)])
async def ingest_movie_form(
    service: IIndexingService = Depends(get_indexing_service),
    titulo: str = Form(..., min_length=1),
    sinopse: str = Form(""),
    descricao: str = Form(""),
    palavras_chave: str = Form(""),
    tema: str = Form(""),
    tags: str = Form(""),
    diretor: str = Form(""),
    movie_id: str | None = Form(None),
    ano: int | None = Form(None, ge=1880, le=2100),
) -> dict[str, Any]:
    """Ingest a single movie via HTML form or multipart/form-data."""
    return await service.ingest_single_movie(
        titulo=titulo,
        sinopse=sinopse,
        descricao=descricao,
        palavras_chave=palavras_chave,
        diretor=diretor,
        movie_id=movie_id,
        ano=ano,
        tema=tema,
        tags=tags,
    )


@router.post("/batch/csv", dependencies=[Depends(require_api_key)])
async def ingest_batch_from_csv(
    file: UploadFile = File(..., description="Catalog CSV (UTF-8)"),
    service: IIndexingService = Depends(get_indexing_service),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """
    Ingest an uploaded catalog CSV. Returns inserted/updated counts and the
    duplicate and invalid rows that were skipped, with their line numbers.
    """
    if not (file.filename or "").lower().endswith(".csv") or (
        file.content_type and file.content_type not in CSV_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Upload a .csv file"
        )
    data = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"CSV larger than {settings.MAX_UPLOAD_BYTES} bytes",
        )
    return await service.ingest_catalog_csv(data)


@router.delete("/movie/{movie_id}", dependencies=[Depends(require_api_key)])
async def delete_movie(
    movie_id: str,
    service: IIndexingService = Depends(get_indexing_service),
) -> dict[str, Any]:
    """Delete a movie by ID; 404 when it does not exist."""
    return await service.delete_movie(movie_id)


@router.get("/count")
async def get_document_count(
    service: IIndexingService = Depends(get_indexing_service),
) -> dict[str, Any]:
    """Total number of indexed movies."""
    return await service.get_document_count()


@router.post("/reset", dependencies=[Depends(require_api_key)])
async def reset_index(
    service: IIndexingService = Depends(get_indexing_service),
) -> dict[str, Any]:
    """Delete every movie in the index (destructive)."""
    return await service.reset_index()
