from functools import lru_cache
import logging
from pathlib import Path
from typing import Annotated, Dict, Any, Optional

from fastapi import Depends
import pandas as pd

from app.providers.pipelines.indexing import IndexingPipeline, get_indexing_pipeline
from app.providers.pipelines.interfaces import IIndexingPipeline
from app.services.interfaces import IIndexingService

logger = logging.getLogger(__name__)


class IndexingService(IIndexingService):
    """
    Service responsible for all indexing-related operations:
    - Single movie ingestion
    - Batch ingestion from CSV
    - Document deletion
    - Document count
    """

    def __init__(self, indexing_pipeline: IndexingPipeline = None):
        self.indexing_pipeline = indexing_pipeline or IndexingPipeline()

    async def ingest_single_movie(
        self,
        titulo: str,
        sinopse: str = "",
        descricao: str = "",
        palavras_chave: str = "",
        diretor: str = "",
        movie_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Ingesting single movie: {titulo}")

            # Build full content
            content_parts = [titulo, sinopse, descricao, palavras_chave]
            content_text = ". ".join([part for part in content_parts if part])

            metadata = {
                "titulo": titulo,
                "sinopse": sinopse,
                "descricao": descricao,
                "palavras_chave": palavras_chave,
                "diretor": diretor,
            }

            result = self.indexing_pipeline.index_single_document(
                content=content_text,
                metadata=metadata,
                doc_id=movie_id,
            )

            return result

        except Exception as e:
            logger.error(f"Single ingestion failed: {e}")
            raise

    async def ingest_movies_from_csv(
        self, csv_path: str = "data/movies.csv"
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Starting batch CSV ingestion: {csv_path}")

            if not Path(csv_path).exists():
                raise FileNotFoundError(f"CSV not found: {csv_path}")

            df = pd.read_csv(csv_path)
            documents = []

            for idx, row in df.iterrows():
                titulo = str(row.get("Título Original", "")).strip()
                direcao = str(
                    row.get("Direção / Um filme de / Uma obra de", "")
                ).strip()
                sinopse = str(row.get("Sinopse", "")).strip()
                descricao = str(row.get("Descrição Completa", "")).strip()
                palavras = str(row.get("Palavras-Chave", "")).strip()

                content_parts = [titulo, sinopse, descricao, palavras]
                content_text = ". ".join([part for part in content_parts if part])

                documents.append(
                    {
                        "doc_id": f"movie-{idx}",
                        "content": content_text,
                        "metadata": {
                            "titulo": titulo,
                            "sinopse": sinopse,
                            "descricao": descricao,
                            "palavras_chave": palavras,
                            "diretor": direcao,
                        },
                    }
                )

            results = self.indexing_pipeline.index_batch_documents(documents)
            return results

        except Exception as e:
            logger.error(f"CSV ingestion failed: {e}")
            raise

    async def delete_movie(self, movie_id: str) -> Dict[str, Any]:
        try:
            deleted = self.indexing_pipeline.delete_document(movie_id)
            return {
                "status": "success" if deleted else "failure",
                "deleted_movie_id": movie_id,
                "deleted": deleted,
            }
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise

    async def get_document_count(self) -> Dict[str, Any]:
        try:
            count = self.indexing_pipeline.count_documents()
            return {"status": "success", "document_count": count}
        except Exception as e:
            logger.error(f"Count failed: {e}")
            raise


@lru_cache()
def get_indexing_service(
    pipeline: Annotated[IndexingPipeline, Depends(get_indexing_pipeline)],
) -> IIndexingService:
    return IndexingService(indexing_pipeline=pipeline)

