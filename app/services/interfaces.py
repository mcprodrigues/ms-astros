from abc import ABC, abstractmethod
from typing import Any

from app.schemas.search import SearchRequest, SearchResponse


class ISearchService(ABC):
    """
    Abstract interface for Search Service.
    Defines methods for document ingestion and semantic search.
    """

    @abstractmethod
    async def semantic_search(self, search_request: SearchRequest) -> SearchResponse:
        """
        Execute semantic search using search pipeline.
        """
        pass


class IIndexingService(ABC):
    @abstractmethod
    async def ingest_single_movie(
        self,
        titulo: str,
        sinopse: str = "",
        descricao: str = "",
        palavras_chave: str = "",
        diretor: str = "",
        movie_id: str = None,
    ) -> dict[str, Any]:
        """
        Ingest a single movie document incrementally.
        """
        pass

    @abstractmethod
    async def ingest_movies_from_csv(self, csv_path: str = "data/movies.csv") -> dict[str, Any]:
        """
        Ingest movies in batch from CSV file.
        """
        pass

    @abstractmethod
    async def delete_movie(self, movie_id: str) -> dict[str, Any]:
        """
        Delete a movie document by its ID.
        """
        pass

    @abstractmethod
    async def get_document_count(self) -> dict[str, Any]:
        """
        Get the total count of documents in the index.
        """
        pass
