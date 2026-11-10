import math

import pytest

from app.domain.catalog_io import read_catalog_csv
from app.domain.movie import (
    InvalidCatalogError,
    Movie,
    clean_text,
    make_movie_id,
    parse_catalog,
    parse_year,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, ""), (math.nan, ""), ("  a \n b  ", "a b"), ("nan", "nan"), (1968, "1968")],
)
def test_clean_text(raw, expected):
    assert clean_text(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), [("1968", 1968), (" c. 2021 ", 2021), ("", None)])
def test_parse_year(raw, expected):
    assert parse_year(raw) == expected


def test_movie_id_is_stable_across_whitespace_and_case():
    assert make_movie_id("Lavra dor", 1968) == make_movie_id("  LAVRA   dor ", 1968)


def test_movie_id_differs_by_year():
    assert make_movie_id("Lavra dor", 1968) != make_movie_id("Lavra dor", 1969)


def test_movie_id_is_a_uuid_independent_of_row_position():
    movie_id = make_movie_id("Sensemayá", 2021)

    assert len(movie_id) == 36
    assert movie_id == make_movie_id("Sensemayá", 2021)


def test_content_includes_director_and_skips_empty_fields():
    movie = Movie.create(titulo="Lavra dor", sinopse="Sindicalismo", diretor="Ana Carolina")

    assert movie.content == "Lavra dor. Direção: Ana Carolina. Sindicalismo"


def test_explicit_movie_id_is_respected():
    assert Movie.create(titulo="X", movie_id="custom").id == "custom"


def test_parse_catalog_resolves_header_with_trailing_space():
    result = parse_catalog(
        ["Título Original", "Direção / Um filme de / Uma obra de "],
        [{"Título Original": "Lavra dor", "Direção / Um filme de / Uma obra de ": "Ana Carolina"}],
    )

    assert result.movies[0].diretor == "Ana Carolina"


def test_parse_catalog_requires_title_column():
    with pytest.raises(InvalidCatalogError, match="Título Original"):
        parse_catalog(["Sinopse"], [])


def test_read_catalog_csv_end_to_end(catalog_csv):
    result = read_catalog_csv(catalog_csv)

    assert [m.titulo for m in result.movies] == ["Lavra dor", "Sensemayá"]
    assert result.movies[0].ano == 1968
    assert result.movies[1].sinopse == ""  # blank cell is '', never 'nan'
    assert [i.line for i in result.duplicates] == [4]
    assert [i.line for i in result.invalid] == [5]


def test_content_includes_theme_and_tags():
    movie = Movie.create(titulo="Bullfight", tema="morte como espetáculo", tags="tourada")

    assert movie.content == "Bullfight. Tema: morte como espetáculo. Tags: tourada"


def test_catalog_maps_theme_and_tags_columns():
    result = parse_catalog(
        ["Título Original", "Tema", "Tags"],
        [{"Título Original": "Ism, ism", "Tema": "intervenção artística", "Tags": "grafite"}],
    )

    assert (result.movies[0].tema, result.movies[0].tags) == ("intervenção artística", "grafite")
