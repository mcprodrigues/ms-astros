from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic-settings for validation and type safety.
    """

    # Weaviate configuration
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_GRPC_HOST: str = "localhost"
    WEAVIATE_GRPC_PORT: int = 50051
    WEAVIATE_INDEX_NAME: str = "AstrosMovies"

    # CSV file path
    CSV_FILE_PATH: str = "data/movies.csv"

    # Embedding model configuration
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    # Search configuration
    DEFAULT_TOP_K: int = 5
    MIN_SCORE_THRESHOLD: float = 0.5

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
