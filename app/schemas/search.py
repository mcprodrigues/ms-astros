from pydantic import BaseModel, ConfigDict, Field

from app.schemas.movie import MovieResponse


class SearchRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "filmes sobre luta no campo e trabalho rural",
                "top_k": 5,
                "min_score": 0.42,
            }
        }
    )

    query: str = Field(..., description="Natural language query", min_length=1, max_length=500)
    top_k: int | None = Field(
        default=None, description="Max results (server default when omitted)", ge=1, le=20
    )
    min_score: float | None = Field(
        default=None,
        description="Minimum cosine similarity, 0–1 (server default when omitted)",
        ge=0.0,
        le=1.0,
    )


class SearchResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "filmes sobre luta no campo e trabalho rural",
                "total_results": 1,
                "results": [
                    {
                        "id": "4dd7d995-aa94-5b73-bc9f-799ed990a4cd",
                        "titulo": "Lavra dor",
                        "sinopse": "Análise poética do sindicalismo rural no Estado de São Paulo",
                        "descricao": "",
                        "palavras_chave": "trabalhador rural, casa de tapera, palha, pasto",
                        "diretor": "Ana Carolina, Paulo Rufino",
                        "score": 0.47,
                    }
                ],
            }
        }
    )

    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Number of results returned")
    results: list[MovieResponse] = Field(..., description="Matching movies, best first")
