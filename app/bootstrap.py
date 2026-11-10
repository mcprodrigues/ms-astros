"""Startup tasks that prepare the index. Must be idempotent."""

import logging
from pathlib import Path

from app.providers.pipelines.interfaces import IEmbedder, IIndexingPipeline
from app.scripts.load_embeddings import EmbeddingLoader

logger = logging.getLogger(__name__)


def load_precomputed_embeddings_if_empty(
    indexing_pipeline: IIndexingPipeline, embedder: IEmbedder, embeddings_path: Path
) -> int:
    """
    Seed an empty index from the precomputed embeddings file.

    Never touches a populated index. Returns the number of documents written
    (0 when skipped). Raises EmbeddingModelMismatchError when the file was
    produced by a different model than `embedder`, failing startup loudly.
    """
    existing = indexing_pipeline.count_documents()
    if existing > 0:
        logger.info("Index already has %d documents; skipping precomputed load", existing)
        return 0

    if not embeddings_path.exists():
        logger.warning("Embeddings file not found: %s; starting with empty index", embeddings_path)
        return 0

    loader = EmbeddingLoader(indexing_pipeline=indexing_pipeline, embedder=embedder)
    written = loader.index_documents(loader.load_from_parquet(embeddings_path))
    logger.info("Indexed %d precomputed embeddings", written)
    return written
