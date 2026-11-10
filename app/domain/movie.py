"""
Canonical movie model and the single mapping from catalog rows to movies.

Every ingestion path (API, CSV upload, offline embedding script) goes through
this module, so content composition and identity cannot drift between them.
"""

import math
import re
import unicodedata
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from app.domain.errors import InvalidCatalogError

# Fixed namespace: changing it changes every movie ID.
MOVIE_ID_NAMESPACE = uuid.UUID("6f1c2b8e-3a5d-4e7f-9b0a-1c2d3e4f5a6b")

# Catalog headers per field. Headers are compared after strip(), and the first
# alias present in the file wins, so renamed columns keep working.
CATALOG_COLUMNS: dict[str, tuple[str, ...]] = {
    "titulo": ("Título Original",),
    "ano": ("Ano de Lançamento",),
    "sinopse": ("Sinopse",),
    "descricao": ("Descrição Completa",),
    "palavras_chave": ("Palavras-Chave",),
    "diretor": ("Direção / Um filme de / Uma obra de",),
}
REQUIRED_COLUMNS = ("titulo",)

METADATA_FIELDS = ("titulo", "sinopse", "descricao", "palavras_chave", "diretor")


def clean_text(value: Any) -> str:
    """Normalize a raw catalog cell: missing/NaN become '', whitespace is collapsed."""
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = unicodedata.normalize("NFC", str(value))
    return re.sub(r"\s+", " ", text).strip()


def parse_year(value: Any) -> int | None:
    match = re.search(r"\b(\d{4})\b", clean_text(value))
    return int(match.group(1)) if match else None


def make_movie_id(titulo: str, ano: int | None) -> str:
    """Deterministic ID from the stable identity of a work: original title + year."""
    key = f"{clean_text(titulo).casefold()}|{ano if ano is not None else ''}"
    return str(uuid.uuid5(MOVIE_ID_NAMESPACE, key))


class Movie(BaseModel):
    id: str
    titulo: str = Field(min_length=1)
    ano: int | None = None
    sinopse: str = ""
    descricao: str = ""
    palavras_chave: str = ""
    diretor: str = ""

    @classmethod
    def create(
        cls,
        titulo: str,
        ano: int | None = None,
        sinopse: str = "",
        descricao: str = "",
        palavras_chave: str = "",
        diretor: str = "",
        movie_id: str | None = None,
    ) -> "Movie":
        titulo = clean_text(titulo)
        return cls(
            id=movie_id or make_movie_id(titulo, ano),
            titulo=titulo,
            ano=ano,
            sinopse=clean_text(sinopse),
            descricao=clean_text(descricao),
            palavras_chave=clean_text(palavras_chave),
            diretor=clean_text(diretor),
        )

    @property
    def content(self) -> str:
        """The text that gets embedded and keyword-indexed."""
        parts = [
            self.titulo,
            self.sinopse,
            self.descricao,
            self.palavras_chave,
            f"Direção: {self.diretor}" if self.diretor else "",
        ]
        return ". ".join(part for part in parts if part)

    @property
    def metadata(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in METADATA_FIELDS}


@dataclass(frozen=True)
class RowIssue:
    line: int  # 1-based line number in the CSV file, header is line 1
    reason: str


@dataclass
class CatalogParseResult:
    movies: list[Movie] = field(default_factory=list)
    duplicates: list[RowIssue] = field(default_factory=list)
    invalid: list[RowIssue] = field(default_factory=list)


def resolve_columns(headers: Iterable[str]) -> dict[str, str]:
    """Map each field to the actual header used in this file."""
    by_stripped = {clean_text(h): h for h in headers}
    resolved = {}
    for name, aliases in CATALOG_COLUMNS.items():
        for alias in aliases:
            if alias in by_stripped:
                resolved[name] = by_stripped[alias]
                break
    missing = [name for name in REQUIRED_COLUMNS if name not in resolved]
    if missing:
        expected = ", ".join(CATALOG_COLUMNS[name][0] for name in missing)
        raise InvalidCatalogError(f"Catalog is missing required column(s): {expected}")
    return resolved


def movie_from_row(row: Mapping[str, Any], columns: Mapping[str, str]) -> Movie:
    def get(name: str) -> Any:
        return row.get(columns[name]) if name in columns else None

    return Movie.create(
        titulo=clean_text(get("titulo")),
        ano=parse_year(get("ano")),
        sinopse=clean_text(get("sinopse")),
        descricao=clean_text(get("descricao")),
        palavras_chave=clean_text(get("palavras_chave")),
        diretor=clean_text(get("diretor")),
    )


def parse_catalog(headers: Iterable[str], rows: Iterable[Mapping[str, Any]]) -> CatalogParseResult:
    """
    Turn catalog rows into movies. Rows without a title are reported as invalid;
    repeated (title, year) pairs keep the first occurrence and report the rest.
    """
    columns = resolve_columns(headers)
    result = CatalogParseResult()
    first_line_by_id: dict[str, int] = {}

    for index, row in enumerate(rows):
        line = index + 2
        if not clean_text(row.get(columns["titulo"])):
            result.invalid.append(RowIssue(line=line, reason="missing title"))
            continue
        movie = movie_from_row(row, columns)
        if movie.id in first_line_by_id:
            result.duplicates.append(
                RowIssue(
                    line=line,
                    reason=f"duplicate of line {first_line_by_id[movie.id]} ({movie.titulo})",
                )
            )
            continue
        first_line_by_id[movie.id] = line
        result.movies.append(movie)

    return result
