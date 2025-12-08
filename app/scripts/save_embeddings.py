"""
Script to generate and save embeddings to disk.
Supports multiple formats: pickle, numpy, parquet.

Usage: python scripts/save_embeddings.py
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List, Any

from app.providers.pipelines.components.embedder import EmbedderComponent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingSaver:
    """
    Generate embeddings from CSV and save to multiple formats.
    """

    def __init__(self):
        self.embedder = EmbedderComponent()
        self.output_dir = Path("data/embeddings")
        self.output_dir.mkdir(exist_ok=True)

    def generate_embeddings_from_csv(self, csv_path: str = "data/movies.csv") -> List[Dict[str, Any]]:
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
            metadata_list.append({
                "id": f"movie_{idx}",
                "titulo": titulo,
                "sinopse": sinopse,
                "descricao": descricao,
                "palavras_chave": palavras,
                "diretor": diretor,
            })

        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedder.encode_batch(texts)

        # Combine everything
        embeddings_data = []
        for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadata_list)):
            embeddings_data.append({
                "id": metadata["id"],
                "content": text,
                "embedding": embedding,
                "metadata": metadata
            })

            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(texts)} embeddings")

        logger.info(f"Generated {len(embeddings_data)} embeddings")
        return embeddings_data

    def save_as_parquet(self, embeddings_data: List[Dict[str, Any]], filename: str = "embeddings.parquet"):
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
                **item["metadata"]
            }
            records.append(record)

        df = pd.DataFrame(records)

        logger.info(f"Saving as parquet: {output_path}")
        df.to_parquet(output_path, compression="snappy", index=False)

        file_size = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Saved {len(embeddings_data)} embeddings as parquet ({file_size:.2f} MB)")

def main():
    """Main execution."""
    saver = EmbeddingSaver()
    embeddings_data = saver.generate_embeddings_from_csv()
    saver.save_as_parquet(embeddings_data)


if __name__ == "__main__":
    main()