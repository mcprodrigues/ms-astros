"""
Generate embeddings for the catalog CSV and save them as parquet.

Usage: uv run python -m app.scripts.save_embeddings
"""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from app.providers.pipelines.interfaces import IEmbedder

logger = logging.getLogger(__name__)


class EmbeddingSaver:
    """
    Generate embeddings from CSV and save to multiple formats.
    """

    def __init__(self, embedder: IEmbedder, output_dir: Path):
        self.embedder = embedder
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_embeddings_from_csv(
        self, csv_path: str = "data/movies.csv"
    ) -> list[dict[str, Any]]:
        """
        Generate embeddings for all movies in CSV.

        Args:
            csv_path: Path to CSV file

        Returns:
            List of dicts with content, embeddings, and metadata
        """
        logger.info(f"Reading CSV: {csv_path}")
        df = pd.read_csv(csv_path)

        texts = []
        metadata_list = []

        for idx, row in df.iterrows():
            titulo = str(row.get("Título Original", "")).strip()
            diretor = str(row.get("Direção / Um filme de / Uma obra de", "")).strip()
            sinopse = str(row.get("Sinopse", "")).strip()
            descricao = str(row.get("Descrição Completa", "")).strip()
            palavras = str(row.get("Palavras-Chave", "")).strip()

            # Build content
            content_parts = [titulo, sinopse, descricao, palavras]
            content_text = ". ".join([c for c in content_parts if c])

            texts.append(content_text)
            metadata_list.append(
                {
                    "id": f"movie_{idx}",
                    "titulo": titulo,
                    "sinopse": sinopse,
                    "descricao": descricao,
                    "palavras_chave": palavras,
                    "diretor": diretor,
                }
            )

        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedder.encode_batch(texts)

        # Combine everything
        embeddings_data = []
        for i, (text, embedding, metadata) in enumerate(
            zip(texts, embeddings, metadata_list, strict=True)
        ):
            embeddings_data.append(
                {
                    "id": metadata["id"],
                    "content": text,
                    "embedding": embedding,
                    "metadata": metadata,
                }
            )

            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(texts)} embeddings")

        logger.info(f"Generated {len(embeddings_data)} embeddings")
        return embeddings_data

    def save_as_parquet(
        self, embeddings_data: list[dict[str, Any]], filename: str = "embeddings.parquet"
    ):
        """
        Save embeddings as parquet (structured, cross-platform).
        Best for: Data pipelines, analytics, cross-platform compatibility.

        File size: Small (compressed)
        Load speed: Fast
        Compatibility: Python, R, Spark, DuckDB, etc.
        """
        output_path = self.output_dir / filename

        # Prepare DataFrame
        records = []
        for item in embeddings_data:
            record = {
                "id": item["id"],
                "content": item["content"],
                "embedding": item["embedding"].tolist(),  # Convert to list for parquet
                **item["metadata"],
            }
            records.append(record)

        df = pd.DataFrame(records)

        logger.info(f"Saving as parquet: {output_path}")
        df.to_parquet(output_path, compression="snappy", index=False)

        file_size = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Saved {len(embeddings_data)} embeddings as parquet ({file_size:.2f} MB)")


def main() -> None:
    from app.dependencies import build_embedder
    from app.settings import Settings

    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    output_path = Path(settings.EMBEDDINGS_PATH)
    saver = EmbeddingSaver(embedder=build_embedder(settings), output_dir=output_path.parent)
    embeddings_data = saver.generate_embeddings_from_csv(settings.CSV_FILE_PATH)
    saver.save_as_parquet(embeddings_data, filename=output_path.name)


if __name__ == "__main__":
    main()
