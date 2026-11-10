"""
Generate embeddings for the catalog CSV and save them as parquet.

Usage: uv run python -m app.scripts.save_embeddings [path/to/catalog.csv]
"""

import logging
import sys
from pathlib import Path
from typing import Any

from app.domain.catalog_io import read_catalog_csv
from app.domain.movie import Movie
from app.providers.embeddings_file import fingerprint_of, write_embeddings_parquet
from app.providers.pipelines.interfaces import IEmbedder

logger = logging.getLogger(__name__)


class EmbeddingSaver:
    """Embeds catalog movies and writes them to a parquet file."""

    def __init__(self, embedder: IEmbedder, output_dir: Path):
        self.embedder = embedder
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_embeddings(self, movies: list[Movie]) -> list[dict[str, Any]]:
        logger.info("Generating embeddings for %d movies", len(movies))
        embeddings = self.embedder.encode_batch([m.content for m in movies])
        return [
            {"id": m.id, "content": m.content, "embedding": e.tolist(), **m.metadata}
            for m, e in zip(movies, embeddings, strict=True)
        ]

    def save_as_parquet(
        self, records: list[dict[str, Any]], filename: str = "embeddings.parquet"
    ) -> Path:
        output_path = self.output_dir / filename
        write_embeddings_parquet(records, output_path, fingerprint_of(self.embedder))
        logger.info("Saved %d embeddings to %s", len(records), output_path)
        return output_path


def main() -> None:
    from app.dependencies import build_embedder
    from app.settings import Settings

    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    csv_path = sys.argv[1] if len(sys.argv) > 1 else settings.CSV_FILE_PATH

    parsed = read_catalog_csv(csv_path)
    for issue in parsed.duplicates + parsed.invalid:
        logger.warning("Skipped CSV line %d: %s", issue.line, issue.reason)

    output_path = Path(settings.EMBEDDINGS_PATH)
    saver = EmbeddingSaver(embedder=build_embedder(settings), output_dir=output_path.parent)
    saver.save_as_parquet(saver.generate_embeddings(parsed.movies), filename=output_path.name)


if __name__ == "__main__":
    main()
