import logging
import pandas as pd
from typing import Dict, Any
from haystack import Document

from app.providers.pipelines.indexing import IndexingPipeline
from app.providers.pipelines.semantic_search import SearchPipeline
from app.settings import settings
from app.schemas.movie import MovieResponse
from app.schemas.search import SearchRequest, SearchResponse

logger = logging.getLogger(__name__)


class SearchService:
    """
    Search service orchestrating business logic for semantic search.
    Handles data indexing and query execution using Haystack pipelines.
    """

    def __init__(self):
        self.indexing_pipeline = IndexingPipeline()
        self.search_pipeline = SearchPipeline()

    async def index_movies_from_csv(self) -> Dict[str, Any]:
        """
        Index movies from CSV file into document store.

        Returns:
            Dict containing indexing status and document count
        """
        try:
            logger.info("Starting movie indexing from CSV...")

            df = pd.read_csv("data/movies.csv")
            documents = []

            for _, row in df.iterrows():
                titulo_original = str(row.get("Título Original", "")).strip()
                direcao = str(
                    row.get("Direção / Um filme de / Uma obra de", "")
                ).strip()
                sinopse = str(row.get("Sinopse", "")).strip()
                descricao = str(row.get("Descrição Completa", "")).strip()
                palavras = str(row.get("Palavras-Chave", "")).strip()

                content_parts = [
                    titulo_original,
                    sinopse,
                    descricao,
                    palavras,
                ]
                content_text = ". ".join([c for c in content_parts if c])

                doc = Document(
                    content=content_text,
                    meta={
                        "titulo": titulo_original,
                        "sinopse": sinopse,
                        "descricao": descricao,
                        "palavras_chave": palavras,
                        "diretor": direcao,
                    },
                )

                documents.append(doc)

            doc_count = self.indexing_pipeline.index_documents(documents)

            return {
                "status": "success",
                "indexed_documents": doc_count,
            }

        except Exception as e:
            logger.error(f"Indexation failed: {e}")
            raise

    async def semantic_search(self, search_request: SearchRequest) -> SearchResponse:
        """
        Execute semantic search using search pipeline.

        Args:
            search_request: Search request with query and parameters

        Returns:
            SearchResponse: Search results with movie information
        """
        try:
            logger.info(f"Executing semantic search for query: {search_request.query}")

            documents = self.search_pipeline.search(
                query=search_request.query, top_k=search_request.top_k
            )

            movie_results = []

            for doc in documents:
                meta = doc.meta
                score = getattr(doc, "score", 1.0)

                if score >= search_request.min_score:
                    movie_results.append(
                        MovieResponse(
                            titulo=meta.get("titulo", ""),
                            sinopse=meta.get("sinopse", ""),
                            descricao=meta.get("descricao", ""),
                            palavras_chave=meta.get("palavras_chave", ""),
                            diretor=meta.get("diretor", ""),
                            score=round(score, 4),
                        )
                    )

            return SearchResponse(
                query=search_request.query,
                total_results=len(movie_results),
                results=movie_results,
            )

        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            raise
