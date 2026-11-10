from app.schemas.search import SearchRequest


async def test_semantic_search_maps_documents_to_response(container):
    await container.indexing_service.ingest_single_movie(
        titulo="Lavra dor", sinopse="sindicalismo rural", diretor="Ana Carolina", movie_id="m1"
    )

    response = await container.search_service.semantic_search(
        SearchRequest(query="sindicalismo", top_k=5, min_score=0.0)
    )

    assert response.total_results == 1
    assert response.results[0].titulo == "Lavra dor"
    assert response.results[0].diretor == "Ana Carolina"
