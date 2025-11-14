from pydantic import BaseModel, Field
from typing import Optional


class Movie(BaseModel):
    """
    Movie schema representing a film document.
    Used for data validation and serialization.
    """

    titulo: str = Field(..., description="Título original do filme")
    sinopse: str = Field(..., description="Sinopse do filme")
    descricao: Optional[str] = Field("", description="Descrição completa")
    palavras_chave: Optional[str] = Field("", description="Palavras-chave")
    diretor: Optional[str] = Field(
        "", description="Direção / Um filme de / Uma obra de"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Lavra dor",
                "sinopse": "Análise poética do sindicalismo rural...",
                # "ano": 1968,
                "diretor": "Ana Carolina, Paulo Rufino",
            }
        }


class MovieResponse(Movie):
    """
    Extended movie schema with search score.
    Used for search result responses.
    """

    score: float = Field(..., description="Similarity score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Lavra dor",
                "sinopse": "Análise poética do sindicalismo rural...",
                # "ano": 1968,
                "diretor": "Ana Carolina, Paulo Rufino",
                "score": 0.89,
            }
        }
