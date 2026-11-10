"""
Load precomputed embeddings from parquet and index them.

Usage: uv run python -m app.scripts.load_embeddings
"""

import logging
from pathlib import Path

import pandas as pd
from haystack import Document

from app.providers.pipelines.interfaces import IIndexingPipeline

logger = logging.getLogger(__name__)

METADATA_FIELDS = ("titulo", "sinopse", "descricao", "palavras_chave", "diretor")


class EmbeddingLoader:
    """Reads precomputed embeddings and writes them through the indexing pipeline."""

    def __init__(self, indexing_pipeline: IIndexingPipeline):
        self.indexing_pipeline = indexing_pipeline

    def load_from_parquet(self, path: Path) -> list[Document]:
        if not path.exists():
            raise FileNotFoundError(f"Parquet file not found: {path}")

        df = pd.read_parquet(path)
        documents = [
            Document(
                id=row["id"],
                content=row["content"],
                embedding=[float(x) for x in row["embedding"]],
                meta={field: row.get(field, "") for field in METADATA_FIELDS},
            )
            for _, row in df.iterrows()
        ]
        logger.info("Loaded %d embeddings from %s", len(documents), path)
        return documents

    def index_documents(self, documents: list[Document]) -> int:
        return self.indexing_pipeline.index_precomputed_documents(documents)


def main() -> None:
    from app.dependencies import build_container
    from app.settings import Settings

    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    container = build_container(settings)
    try:
        loader = EmbeddingLoader(indexing_pipeline=container.indexing_pipeline)
        count = loader.index_documents(loader.load_from_parquet(Path(settings.EMBEDDINGS_PATH)))
        logger.info("Indexed %d documents", count)
    finally:
        container.close()


if __name__ == "__main__":
    main()
