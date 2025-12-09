"""
Script to load embeddings from saved files and index them.

Usage: python scripts/load_embeddings.py
"""

import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any

from haystack import Document
from app.providers.pipelines.indexing import IndexingPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingLoader:
    """
    Load embeddings from disk and index them.
    """

    def __init__(self):
        self.indexing_pipeline = IndexingPipeline()
        self.embeddings_dir = Path("data/embeddings")

    def load_from_parquet(self, filename: str = "embeddings.parquet") -> List[Dict[str, Any]]:
        """
        Load embeddings from parquet file.

        Args:
            filename: Parquet filename

        Returns:
            List of embedding data dicts
        """
        filepath = self.embeddings_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Parquet file not found: {filepath}")

        logger.info(f"Loading from parquet: {filepath}")
        df = pd.read_parquet(filepath)

        embeddings_data = []
        for _, row in df.iterrows():
            embeddings_data.append({
                "id": row["id"],
                "content": row["content"],
                "embedding": np.array(row["embedding"]),  # Convert back to numpy array
                "metadata": {
                    "titulo": row.get("titulo", ""),
                    "sinopse": row.get("sinopse", ""),
                    "descricao": row.get("descricao", ""),
                    "palavras_chave": row.get("palavras_chave", ""),
                    "diretor": row.get("diretor", ""),
                }
            })

        logger.info(f"Loaded {len(embeddings_data)} embeddings from parquet")
        return embeddings_data

    def index_precomputed_embeddings(self, embeddings_data: List[Dict[str, Any]]) -> int:
        """
        Index with precomputed embeddings (bypassing embedding generation).

        Args:
            embeddings_data: List of embedding data dicts

        Returns:
            Number of documents indexed
        """
        logger.info(f"Indexing {len(embeddings_data)} documents with precomputed embeddings...")

        # Create Haystack Documents with embeddings
        documents = []
        for item in embeddings_data:
            doc = Document(
                id=item["id"],
                content=item["content"],
                embedding=item["embedding"].tolist() if isinstance(item["embedding"], np.ndarray) else item["embedding"],
                meta=item["metadata"]
            )
            documents.append(doc)

        # Write directly to document store (bypassing pipeline to preserve embeddings)
        doc_store = self.indexing_pipeline.document_store_provider.get_document_store()
        doc_store.write_documents(documents)

        logger.info(f"✓ Indexed {len(documents)} documents with precomputed embeddings")
        return len(documents)


def main():
    """Main execution."""
    logger.info("=" * 60)
    logger.info("Loading and Indexing Embeddings")
    logger.info("=" * 60)

    loader = EmbeddingLoader()

    embeddings_data = loader.load_from_parquet()

    # Index with precomputed embeddings
    count = loader.index_precomputed_embeddings(embeddings_data)

    logger.info("\n" + "=" * 60)
    logger.info(f"✓ Successfully indexed {count} documents")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()