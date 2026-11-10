async def test_ingest_single_movie_builds_content_and_metadata(container, store_provider):
    result = await container.indexing_service.ingest_single_movie(
        titulo="Lavra dor", sinopse="Análise poética", diretor="Ana Carolina", movie_id="m1"
    )

    assert result["document_id"] == "m1"
    doc = store_provider.store.filter_documents()[0]
    assert doc.content == "Lavra dor. Análise poética"
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
