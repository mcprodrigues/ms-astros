import pytest

from app.domain.errors import InvalidCatalogError, MovieNotFoundError, StoreUnavailableError


async def test_ingest_single_movie_builds_content_and_metadata(container, store_provider):
    result = await container.indexing_service.ingest_single_movie(
        titulo="Lavra dor", sinopse="Análise poética", diretor="Ana Carolina", movie_id="m1"
    )

    assert result["document_id"] == "m1"
    doc = store_provider.store.filter_documents()[0]
    assert doc.content == "Lavra dor. Direção: Ana Carolina. Análise poética"
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


async def test_ingest_csv_reports_inserted_duplicates_and_invalid_rows(container, catalog_csv):
    result = await container.indexing_service.ingest_catalog_csv(catalog_csv.read_bytes())

    assert (result["indexed_count"], result["inserted"], result["updated"]) == (2, 2, 0)
    assert result["duplicates"] == [{"line": 4, "reason": "duplicate of line 2 (Lavra dor)"}]
    assert result["invalid_rows"] == [{"line": 5, "reason": "missing title"}]


async def test_ingest_csv_twice_is_idempotent_and_reports_updates(container, catalog_csv):
    service = container.indexing_service
    await service.ingest_catalog_csv(catalog_csv.read_bytes())

    second = await service.ingest_catalog_csv(catalog_csv.read_bytes())

    assert (second["inserted"], second["updated"]) == (0, 2)
    assert (await service.get_document_count())["document_count"] == 2


async def test_ingest_csv_fills_director_from_header_with_trailing_space(
    container, store_provider, catalog_csv
):
    await container.indexing_service.ingest_catalog_csv(catalog_csv.read_bytes())

    docs = store_provider.store.filter_documents()
    directors = {d.meta["titulo"]: d.meta["diretor"] for d in docs}
    assert directors["Lavra dor"] == "Ana Carolina, Paulo Rufino"


@pytest.mark.parametrize("data", [b"", b"\xff\xfe not utf-8", b"Sinopse\nsem coluna de titulo\n"])
async def test_ingest_csv_rejects_unreadable_or_invalid_catalog(container, data):
    with pytest.raises(InvalidCatalogError):
        await container.indexing_service.ingest_catalog_csv(data)


async def test_delete_missing_movie_raises_not_found(container):
    with pytest.raises(MovieNotFoundError):
        await container.indexing_service.delete_movie("does-not-exist")


async def test_delete_existing_movie(container):
    await container.indexing_service.ingest_single_movie(titulo="A", movie_id="a")

    result = await container.indexing_service.delete_movie("a")

    assert result == {"status": "success", "deleted_movie_id": "a"}
    assert (await container.indexing_service.get_document_count())["document_count"] == 0


async def test_count_raises_store_unavailable_instead_of_zero(container, store_provider):
    def broken():
        raise ConnectionError("weaviate down")

    store_provider.store.count_documents = broken
    store_provider.ready = False

    with pytest.raises(StoreUnavailableError):
        await container.indexing_service.get_document_count()


async def test_blocking_pipeline_work_does_not_block_event_loop(container, monkeypatch):
    import asyncio
    import time

    def slow_count():
        time.sleep(0.3)
        return 0

    monkeypatch.setattr(container.indexing_pipeline, "count_documents", slow_count)
    ticks = 0

    async def ticker():
        nonlocal ticks
        for _ in range(5):
            await asyncio.sleep(0.02)
            ticks += 1

    await asyncio.gather(container.indexing_service.get_document_count(), ticker())

    assert ticks == 5  # the loop kept running while the count blocked a worker thread
