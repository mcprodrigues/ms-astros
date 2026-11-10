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

    # Data
    CSV_FILE_PATH: str = "data/movies.csv"
    EMBEDDINGS_PATH: str = "data/embeddings/embeddings.parquet"

    # Embedding model (must match the model that produced EMBEDDINGS_PATH)
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Search
    DEFAULT_TOP_K: int = 5
    # Provisional, from sampled real queries; recalibrate on the golden set.
    MIN_SCORE_THRESHOLD: float = 0.42
