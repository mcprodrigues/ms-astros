import asyncio
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.domain.catalog_io import read_catalog_csv
from app.domain.movie import Movie
from app.providers.pipelines.interfaces import IIndexingPipeline
from app.services.interfaces import IIndexingService

logger = logging.getLogger(__name__)


class IndexingService(IIndexingService):
    """Movie ingestion, deletion, counting and index reset."""

    def __init__(self, indexing_pipeline: IIndexingPipeline):
        self.indexing_pipeline = indexing_pipeline

    async def ingest_single_movie(
        self,
        titulo: str,
        sinopse: str = "",
        descricao: str = "",
        palavras_chave: str = "",
        diretor: str = "",
        movie_id: str | None = None,
        ano: int | None = None,
    ) -> dict[str, Any]:
        movie = Movie.create(
            titulo=titulo,
            ano=ano,
            sinopse=sinopse,
            descricao=descricao,
            palavras_chave=palavras_chave,
            diretor=diretor,
            movie_id=movie_id,
        )
        return self.indexing_pipeline.index_single_document(
            content=movie.content, metadata=movie.metadata, doc_id=movie.id
        )

    async def ingest_movies_from_csv(self, csv_path: str) -> dict[str, Any]:
        if not await asyncio.to_thread(Path(csv_path).exists):
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        parsed = read_catalog_csv(csv_path)
        logger.info(
            "Parsed catalog: %d movies, %d duplicates, %d invalid rows",
            len(parsed.movies),
            len(parsed.duplicates),
            len(parsed.invalid),
        )
        result = (
            self.indexing_pipeline.index_batch_documents(
                [
                    {"doc_id": m.id, "content": m.content, "metadata": m.metadata}
                    for m in parsed.movies
                ]
            )
            if parsed.movies
            else {"status": "success", "indexed_count": 0, "total_documents": 0}
        )
        return {
            **result,
            "duplicates": [asdict(issue) for issue in parsed.duplicates],
            "invalid_rows": [asdict(issue) for issue in parsed.invalid],
        }

    async def delete_movie(self, movie_id: str) -> dict[str, Any]:
        deleted = self.indexing_pipeline.delete_document(movie_id)
        return {
            "status": "success" if deleted else "failure",
            "deleted_movie_id": movie_id,
            "deleted": deleted,
        }

    async def get_document_count(self) -> dict[str, Any]:
        return {"status": "success", "document_count": self.indexing_pipeline.count_documents()}

    async def reset_index(self) -> dict[str, Any]:
        self.indexing_pipeline.reset_index()
        return {"status": "success", "message": "Index reset complete. All documents deleted."}

    async def is_ready(self) -> bool:
        return self.indexing_pipeline.is_ready()
