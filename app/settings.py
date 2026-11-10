from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables (and `.env`).
    This is the only place configuration is read.
    """

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Weaviate
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_GRPC_PORT: int = 50051
    WEAVIATE_INDEX_NAME: str = "AstrosMovies"
    WEAVIATE_CONNECT_ATTEMPTS: int = 10
    WEAVIATE_CONNECT_BACKOFF_SECONDS: float = 1.0
    WEAVIATE_QUERY_TIMEOUT_SECONDS: float = 10.0
    WEAVIATE_INSERT_TIMEOUT_SECONDS: float = 60.0

    # Security. Write/destructive routes require X-API-Key; when API_KEY is
    # unset they are disabled (fail closed).
    API_KEY: SecretStr | None = None
    CORS_ALLOW_ORIGINS: list[str] = []
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    # Data
    CSV_FILE_PATH: str = "data/movies.csv"
    EMBEDDINGS_PATH: str = "data/embeddings/embeddings.parquet"

    # Embedding model (must match the model that produced EMBEDDINGS_PATH)
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Search
    DEFAULT_TOP_K: int = 5
    # Calibrated on the golden set (docs/evaluation/v1-baseline.md): the lowest
    # threshold at which no out-of-domain query returns results.
    MIN_SCORE_THRESHOLD: float = 0.42
