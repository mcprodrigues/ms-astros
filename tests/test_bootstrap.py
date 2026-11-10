import pandas as pd

from app.bootstrap import load_precomputed_embeddings_if_empty
from tests.fakes import make_document


def write_parquet(path, ids):
    pd.DataFrame(
        [
            {
                "id": doc_id,
                "content": f"filme {doc_id}",
                "embedding": [0.1, 0.2, 0.3, 0.4],
                "titulo": f"filme {doc_id}",
                "sinopse": "",
                "descricao": "",
                "palavras_chave": "",
                "diretor": "",
            }
            for doc_id in ids
        ]
    ).to_parquet(path, index=False)


def test_loads_embeddings_into_empty_index(container, tmp_path):
    path = tmp_path / "embeddings.parquet"
    write_parquet(path, ["a", "b"])

    written = load_precomputed_embeddings_if_empty(container.indexing_pipeline, path)

    assert written == 2
    assert container.indexing_pipeline.count_documents() == 2


def test_never_touches_a_populated_index(container, tmp_path):
    container.indexing_pipeline.index_precomputed_documents([make_document("existing", "X")])
    path = tmp_path / "embeddings.parquet"
    write_parquet(path, ["a", "b"])

    written = load_precomputed_embeddings_if_empty(container.indexing_pipeline, path)

    assert written == 0
    assert container.indexing_pipeline.count_documents() == 1


def test_running_twice_does_not_duplicate(container, tmp_path):
    path = tmp_path / "embeddings.parquet"
    write_parquet(path, ["a", "b"])

    load_precomputed_embeddings_if_empty(container.indexing_pipeline, path)
    load_precomputed_embeddings_if_empty(container.indexing_pipeline, path)

    assert container.indexing_pipeline.count_documents() == 2


def test_missing_file_leaves_index_empty(container, tmp_path):
    written = load_precomputed_embeddings_if_empty(
        container.indexing_pipeline, tmp_path / "missing.parquet"
    )

    assert written == 0
    assert container.indexing_pipeline.count_documents() == 0
