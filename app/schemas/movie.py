"""Movie request/response schemas."""

from pydantic import BaseModel, ConfigDict, Field

_EXAMPLE = {
    "titulo": "Entrevista Com o Vampiro",
    "sinopse": "Um jornalista entrevista um jovem que afirma ser vampiro",
    "descricao": "Em flash-back, conhecemos Louis de Pointe du Lac, um vampiro que....",
    "palavras_chave": "drama, suspense, romance gotico",
    "diretor": "Neil Jordan",
}


class MovieUpload(BaseModel):
    """A single movie for incremental ingestion."""

    model_config = ConfigDict(json_schema_extra={"example": {**_EXAMPLE, "ano": 1994}})

    titulo: str = Field(..., min_length=1, description="Original title")
    ano: int | None = Field(
        default=None, ge=1880, le=2100, description="Release year (part of the movie identity)"
    )
    sinopse: str = Field(default="", description="Movie synopsis")
    descricao: str = Field(default="", description="Full movie description")
    palavras_chave: str = Field(default="", description="Keywords or tags")
    diretor: str = Field(default="", description="Director name")
    movie_id: str | None = Field(
        default=None,
        description="Custom movie ID; derived from title + year when not provided",
    )


class MovieResponse(BaseModel):
    """A search result."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"id": "0b6f0f8e-5c1d-5d2e-9a3b-7c4d5e6f7a8b", **_EXAMPLE, "score": 0.61}
        }
    )

    id: str = Field(description="Movie ID")
    titulo: str
    sinopse: str
    descricao: str
    palavras_chave: str
    diretor: str
    score: float = Field(description="Cosine similarity between query and movie (-1 to 1)")
