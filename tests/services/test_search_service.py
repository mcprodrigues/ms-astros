import pytest

from app.schemas.search import SearchRequest


@pytest.fixture
async def indexed(container):
    await container.indexing_service.ingest_single_movie(
        titulo="Lavra dor", sinopse="sindicalismo rural", diretor="Ana Carolina", movie_id="m1"
    )
    await container.indexing_service.ingest_single_movie(
        titulo="Sensemayá", sinopse="férias de família no méxico", movie_id="m2"
    )
    return container


async def test_maps_documents_to_response_with_id(indexed):
    response = await indexed.search_service.semantic_search(
        SearchRequest(query="luta no campo", min_score=0.0)
    )

    top = response.results[0]
    assert (top.id, top.titulo, top.diretor) == ("m1", "Lavra dor", "Ana Carolina")


async def test_server_default_min_score_filters_unrelated_movies(indexed):
    response = await indexed.search_service.semantic_search(SearchRequest(query="luta no campo"))

    assert [r.id for r in response.results] == ["m1"]
    assert response.total_results == 1


async def test_explicit_zero_min_score_returns_everything(indexed):
    response = await indexed.search_service.semantic_search(
        SearchRequest(query="luta no campo", min_score=0.0)
    )

    assert response.total_results == 2


async def test_server_default_top_k_applies_when_omitted(indexed):
    indexed.search_service.default_top_k = 1

    response = await indexed.search_service.semantic_search(
        SearchRequest(query="luta no campo", min_score=0.0)
    )

    assert response.total_results == 1


async def test_response_includes_theme_and_tags(container):
    await container.indexing_service.ingest_single_movie(
        titulo="Lavra dor", tema="reforma agrária", tags="campo, luta", movie_id="m1"
    )

    response = await container.search_service.semantic_search(
        SearchRequest(query="luta no campo", min_score=0.0)
    )

    assert (response.results[0].tema, response.results[0].tags) == (
        "reforma agrária",
        "campo, luta",
    )
