import pandas as pd

from app.domain.catalog_io import read_catalog_csv
from app.scripts.save_embeddings import EmbeddingSaver
from tests.fakes import FakeEmbedder


def test_saver_writes_parquet_with_mapper_ids(tmp_path, catalog_csv):
    movies = read_catalog_csv(catalog_csv).movies
    saver = EmbeddingSaver(embedder=FakeEmbedder(), output_dir=tmp_path)

    path = saver.save_as_parquet(saver.generate_embeddings(movies))

    df = pd.read_parquet(path)
    assert df["id"].tolist() == [m.id for m in movies]
    assert df["diretor"].tolist()[0] == "Ana Carolina, Paulo Rufino"
