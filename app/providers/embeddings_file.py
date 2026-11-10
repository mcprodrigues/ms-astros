"""
The precomputed embeddings parquet file.

The file records which model produced its vectors (name + dimension) in the
parquet schema metadata. Loading vectors produced by a different model than
the one embedding queries would silently break search, so it is refused.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.domain.errors import EmbeddingModelMismatchError

_MODEL_KEY = b"astros.embedding_model"
_DIM_KEY = b"astros.embedding_dim"


@dataclass(frozen=True)
class EmbeddingFingerprint:
    model_name: str
    dimension: int


def write_embeddings_parquet(
    records: list[dict[str, Any]], path: Path, fingerprint: EmbeddingFingerprint
) -> None:
    table = pa.Table.from_pandas(pd.DataFrame(records), preserve_index=False)
    metadata = {
        **(table.schema.metadata or {}),
        _MODEL_KEY: fingerprint.model_name.encode(),
        _DIM_KEY: str(fingerprint.dimension).encode(),
    }
    pq.write_table(table.replace_schema_metadata(metadata), path, compression="snappy")


def read_fingerprint(path: Path) -> EmbeddingFingerprint | None:
    metadata = pq.read_schema(path).metadata or {}
    if _MODEL_KEY not in metadata or _DIM_KEY not in metadata:
        return None
    return EmbeddingFingerprint(
        model_name=metadata[_MODEL_KEY].decode(), dimension=int(metadata[_DIM_KEY].decode())
    )


def read_embeddings_parquet(path: Path, expected: EmbeddingFingerprint) -> pd.DataFrame:
    """Read the file, refusing it unless it was produced by the `expected` model."""
    actual = read_fingerprint(path)
    if actual is None:
        raise EmbeddingModelMismatchError(
            f"{path} has no embedding model fingerprint; regenerate it with "
            "`uv run python -m app.scripts.save_embeddings`"
        )
    if actual != expected:
        raise EmbeddingModelMismatchError(
            f"{path} was produced by {actual.model_name} (dim={actual.dimension}) but the "
            f"configured model is {expected.model_name} (dim={expected.dimension}); "
            "regenerate the embeddings and reindex"
        )
    return pd.read_parquet(path)


def fingerprint_of(embedder: Any) -> EmbeddingFingerprint:
    return EmbeddingFingerprint(
        model_name=embedder.model_name, dimension=embedder.get_embedding_dimension()
    )
