async def test_ingest_single_movie_builds_content_and_metadata(container, store_provider):
    result = await container.indexing_service.ingest_single_movie(
        titulo="Lavra dor", sinopse="Análise poética", diretor="Ana Carolina", movie_id="m1"
    )

    assert result["document_id"] == "m1"
    doc = store_provider.store.filter_documents()[0]
    assert doc.content == "Lavra dor. Análise poética. Direção: Ana Carolina"
    assert doc.meta["diretor"] == "Ana Carolina"


async def test_reset_index_empties_the_index(container):
    await container.indexing_service.ingest_single_movie(titulo="A", movie_id="a")

    result = await container.indexing_service.reset_index()

    assert result["status"] == "success"
    assert (await container.indexing_service.get_document_count())["document_count"] == 0


async def test_is_ready_reflects_store(container, store_provider):
    assert await container.indexing_service.is_ready() is True
    store_provider.ready = False
    assert await container.indexing_service.is_ready() is False


async def test_same_title_and_year_reingested_keeps_one_document(container):
    service = container.indexing_service
    await service.ingest_single_movie(titulo="Lavra dor", ano=1968)
    await service.ingest_single_movie(titulo="  Lavra   dor ", ano=1968, sinopse="atualizada")

    assert (await service.get_document_count())["document_count"] == 1


async def test_ingest_csv_reports_duplicates_and_invalid_rows(container, catalog_csv):
    result = await container.indexing_service.ingest_movies_from_csv(str(catalog_csv))

    assert result["indexed_count"] == 2
    assert result["duplicates"] == [{"line": 4, "reason": "duplicate of line 2 (Lavra dor)"}]
    assert result["invalid_rows"] == [{"line": 5, "reason": "missing title"}]


async def test_ingest_csv_twice_is_idempotent(container, catalog_csv):
    await container.indexing_service.ingest_movies_from_csv(str(catalog_csv))
    await container.indexing_service.ingest_movies_from_csv(str(catalog_csv))

    assert (await container.indexing_service.get_document_count())["document_count"] == 2


async def test_ingest_csv_fills_director_from_header_with_trailing_space(
    container, store_provider, catalog_csv
):
    await container.indexing_service.ingest_movies_from_csv(str(catalog_csv))

    directors = {
        d.meta["titulo"]: d.meta["diretor"] for d in store_provider.store.filter_documents()
    }
    assert directors["Lavra dor"] == "Ana Carolina, Paulo Rufino"


async def test_ingest_csv_missing_file_raises(container, tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        await container.indexing_service.ingest_movies_from_csv(str(tmp_path / "nope.csv"))
