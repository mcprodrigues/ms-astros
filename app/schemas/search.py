from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.movie import MovieResponse


class SearchRequest(BaseModel):
    """
    Search request schema.
    Defines the structure for semantic search queries.
    """

    query: str = Field(
        ..., description="Search query text", min_length=1, max_length=500
    )
    top_k: Optional[int] = Field(
        default=5, description="Number of results to return", ge=1, le=20
    )
    min_score: Optional[float] = Field(
        default=0.5, description="Minimum similarity score threshold", ge=0.0, le=1.0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "filmes sobre sindicalismo e trabalho rural",
                "top_k": 5,
                "min_score": 0.5,
            }
        }


class SearchResponse(BaseModel):
    """
    Search response schema.
    Contains search results and metadata.
    """

    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Total number of results found")
    results: List[MovieResponse] = Field(..., description="List of matching movies")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "filmes sobre sindicalismo",
                "total_results": 2,
                "results": [
                    {
                        "titulo": "Lavra dor",
                        "sinopse": "Análise poética...",
                        "ano": 1968,
                        "diretor": "Ana Carolina",
                        "score": 0.89,
                    }
                ],
            }
        }
