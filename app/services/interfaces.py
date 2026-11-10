from abc import ABC, abstractmethod
from typing import Any

from app.schemas.search import SearchRequest, SearchResponse


class ISearchService(ABC):
    @abstractmethod
    async def semantic_search(self, search_request: SearchRequest) -> SearchResponse:
        """Run a search and map results to the response schema."""


class IIndexingService(ABC):
    @abstractmethod
    async def ingest_single_movie(
        self,
        titulo: str,
        sinopse: str = "",
        descricao: str = "",
        palavras_chave: str = "",
        diretor: str = "",
        movie_id: str | None = None,
    ) -> dict[str, Any]:
        """Ingest a single movie document incrementally."""

    @abstractmethod
    async def ingest_movies_from_csv(self, csv_path: str) -> dict[str, Any]:
        """Ingest movies in batch from a CSV file."""

    @abstractmethod
    async def delete_movie(self, movie_id: str) -> dict[str, Any]:
        """Delete a movie document by its ID."""

    @abstractmethod
    async def get_document_count(self) -> dict[str, Any]:
        """Total count of documents in the index."""

    @abstractmethod
    async def reset_index(self) -> dict[str, Any]:
        """Delete every document in the index (destructive)."""

    @abstractmethod
    async def is_ready(self) -> bool:
        """True when the index backend is reachable."""
