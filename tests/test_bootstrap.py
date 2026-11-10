import pandas as pd
import pytest

from app.bootstrap import load_precomputed_embeddings_if_empty
from app.providers.embeddings_file import (
    EmbeddingFingerprint,
    EmbeddingModelMismatchError,
    write_embeddings_parquet,
)
from tests.fakes import DIM, FakeEmbedder, make_document

FAKE_FINGERPRINT = EmbeddingFingerprint(FakeEmbedder.model_name, DIM)


def write_parquet(path, ids, fingerprint=FAKE_FINGERPRINT):
    write_embeddings_parquet(
        [
            {
                "id": doc_id,
                "content": f"filme {doc_id}",
                "embedding": [0.1] * DIM,
                "titulo": f"filme {doc_id}",
                "sinopse": "",
                "descricao": "",
                "palavras_chave": "",
                "diretor": "",
            }
            for doc_id in ids
        ],
        path,
        fingerprint,
    )


def load(container, path):
    return load_precomputed_embeddings_if_empty(
        container.indexing_pipeline, container.embedder, path
    )


def test_loads_embeddings_into_empty_index(container, tmp_path):
    path = tmp_path / "embeddings.parquet"
    write_parquet(path, ["a", "b"])

    written = load(container, path)

    assert written == 2
    assert container.indexing_pipeline.count_documents() == 2


def test_never_touches_a_populated_index(container, tmp_path):
    container.indexing_pipeline.index_precomputed_documents([make_document("existing", "X")])
    path = tmp_path / "embeddings.parquet"
    write_parquet(path, ["a", "b"])

    written = load(container, path)

    assert written == 0
    assert container.indexing_pipeline.count_documents() == 1


def test_running_twice_does_not_duplicate(container, tmp_path):
    path = tmp_path / "embeddings.parquet"
    write_parquet(path, ["a", "b"])

    load(container, path)
    load(container, path)

    assert container.indexing_pipeline.count_documents() == 2


def test_missing_file_leaves_index_empty(container, tmp_path):
    written = load(container, tmp_path / "missing.parquet")

    assert written == 0
    assert container.indexing_pipeline.count_documents() == 0


def test_refuses_file_from_another_model(container, tmp_path):
    path = tmp_path / "embeddings.parquet"
    write_parquet(path, ["a"], EmbeddingFingerprint("some-other-model", DIM))

    with pytest.raises(EmbeddingModelMismatchError, match="some-other-model"):
        load(container, path)
    assert container.indexing_pipeline.count_documents() == 0


def test_refuses_file_with_other_dimension(container, tmp_path):
    path = tmp_path / "embeddings.parquet"
    write_parquet(path, ["a"], EmbeddingFingerprint(FakeEmbedder.model_name, 768))

    with pytest.raises(EmbeddingModelMismatchError, match="dim=768"):
        load(container, path)


def test_refuses_legacy_file_without_fingerprint(container, tmp_path):
    path = tmp_path / "embeddings.parquet"
    pd.DataFrame([{"id": "a", "content": "x", "embedding": [0.1] * DIM}]).to_parquet(path)

    with pytest.raises(EmbeddingModelMismatchError, match="no embedding model fingerprint"):
        load(container, path)
