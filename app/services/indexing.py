import asyncio
import io
import logging
from dataclasses import asdict
from typing import Any

from app.domain.catalog_io import read_catalog_csv
from app.domain.errors import MovieNotFoundError
from app.domain.movie import Movie
from app.providers.pipelines.interfaces import IIndexingPipeline
from app.services.interfaces import IIndexingService

logger = logging.getLogger(__name__)


class IndexingService(IIndexingService):
    """
    Movie ingestion, deletion, counting and index reset.

    Pipeline calls are blocking (model inference, store I/O), so they run in
    worker threads and never block the event loop.
    """

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
        tema: str = "",
        tags: str = "",
    ) -> dict[str, Any]:
        movie = Movie.create(
            titulo=titulo,
            ano=ano,
            sinopse=sinopse,
            descricao=descricao,
            palavras_chave=palavras_chave,
            diretor=diretor,
            movie_id=movie_id,
            tema=tema,
            tags=tags,
        )
        return await asyncio.to_thread(
            self.indexing_pipeline.index_single_document,
            content=movie.content,
            metadata=movie.metadata,
            doc_id=movie.id,
        )

    async def ingest_catalog_csv(self, data: bytes) -> dict[str, Any]:
        parsed = await asyncio.to_thread(read_catalog_csv, io.BytesIO(data))
        logger.info(
            "Parsed catalog: %d movies, %d duplicates, %d invalid rows",
            len(parsed.movies),
            len(parsed.duplicates),
            len(parsed.invalid),
        )

        before = await asyncio.to_thread(self.indexing_pipeline.count_documents)
        indexed = 0
        if parsed.movies:
            result = await asyncio.to_thread(
                self.indexing_pipeline.index_batch_documents,
                [
                    {"doc_id": m.id, "content": m.content, "metadata": m.metadata}
                    for m in parsed.movies
                ],
            )
            indexed = result["indexed_count"]
        after = await asyncio.to_thread(self.indexing_pipeline.count_documents)
        inserted = after - before

        return {
            "status": "success",
            "indexed_count": indexed,
            "inserted": inserted,
            "updated": indexed - inserted,
            "duplicates": [asdict(issue) for issue in parsed.duplicates],
            "invalid_rows": [asdict(issue) for issue in parsed.invalid],
        }

    async def delete_movie(self, movie_id: str) -> dict[str, Any]:
        if not await asyncio.to_thread(self.indexing_pipeline.delete_document, movie_id):
            raise MovieNotFoundError(movie_id)
        return {"status": "success", "deleted_movie_id": movie_id}

    async def get_document_count(self) -> dict[str, Any]:
        count = await asyncio.to_thread(self.indexing_pipeline.count_documents)
        return {"status": "success", "document_count": count}

    async def reset_index(self) -> dict[str, Any]:
        await asyncio.to_thread(self.indexing_pipeline.reset_index)
        return {"status": "success", "message": "Index reset complete. All documents deleted."}

    async def is_ready(self) -> bool:
        return await asyncio.to_thread(self.indexing_pipeline.is_ready)
