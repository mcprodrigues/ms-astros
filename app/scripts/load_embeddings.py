"""
Load precomputed embeddings from parquet and index them.

Usage: uv run python -m app.scripts.load_embeddings
"""

import logging
from pathlib import Path

from haystack import Document

from app.domain.movie import METADATA_FIELDS
from app.providers.embeddings_file import fingerprint_of, read_embeddings_parquet
from app.providers.pipelines.interfaces import IEmbedder, IIndexingPipeline

logger = logging.getLogger(__name__)


class EmbeddingLoader:
    """Reads precomputed embeddings and writes them through the indexing pipeline."""

    def __init__(self, indexing_pipeline: IIndexingPipeline, embedder: IEmbedder):
        self.indexing_pipeline = indexing_pipeline
        self.embedder = embedder

    def load_from_parquet(self, path: Path) -> list[Document]:
        """Raises EmbeddingModelMismatchError if the file came from another model."""
        if not path.exists():
            raise FileNotFoundError(f"Parquet file not found: {path}")

        df = read_embeddings_parquet(path, expected=fingerprint_of(self.embedder))
        documents = [
            Document(
                id=row["id"],
                content=row["content"],
                embedding=[float(x) for x in row["embedding"]],
                meta={name: row.get(name, "") for name in METADATA_FIELDS},
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
        loader = EmbeddingLoader(
            indexing_pipeline=container.indexing_pipeline, embedder=container.embedder
        )
        count = loader.index_documents(loader.load_from_parquet(Path(settings.EMBEDDINGS_PATH)))
        logger.info("Indexed %d documents", count)
    finally:
        container.close()


if __name__ == "__main__":
    main()
