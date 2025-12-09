"""
Movie data schemas for requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional


class MovieUpload(BaseModel):
    """
    Schema for uploading a single movie document.
    Used for incremental ingestion via API.
    """

    titulo: str = Field(..., description="Movie title")
    sinopse: str = Field(default="", description="Movie synopsis")
    descricao: str = Field(default="", description="Full movie description")
    palavras_chave: str = Field(default="", description="Keywords or tags")
    diretor: str = Field(default="", description="Director name")
    movie_id: Optional[str] = Field(
        default=None, description="Custom movie ID (auto-generated if not provided)"
    )

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
