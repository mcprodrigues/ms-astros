"""
Movie data schemas for requests and responses.
"""

from pydantic import BaseModel, Field


class MovieUpload(BaseModel):
    """
    Schema for uploading a single movie document.
    Used for incremental ingestion via API.
    """

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

    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Entrevista Com o Vampiro",
                "ano": 1994,
                "sinopse": "Um jornalista entrevista um jovem que afirma ser vampiro",
                "descricao": "Em flash-back, conhecemos Louis de Pointe du Lac, um vampiro que....",
                "palavras_chave": "drama, suspense, romance gotico",
                "diretor": "Neil Jordan",
            }
        }


class MovieResponse(BaseModel):
    """
    Schema for movie search results.
    """

    titulo: str
    sinopse: str
    descricao: str
    palavras_chave: str
    diretor: str
    score: float = Field(description="Relevance score from search")

    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Entrevista Com o Vampiro",
                "sinopse": "Um jornalista entrevista um jovem que afirma ser vampiro",
                "descricao": "Em flash-back, conhecemos Louis de Pointe du Lac, um vampiro que....",
                "palavras_chave": "drama, suspense, romance gotico",
                "diretor": "Neil Jordan",
                "movie_id": "entrevista_com_o_vampiro_1994",
            }
        }
