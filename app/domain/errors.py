"""
Domain exceptions. They carry no HTTP knowledge; the API layer maps them to
status codes in `app.error_handlers`.
"""


class AstrosError(Exception):
    """Base class for expected, user-facing failures."""


class MovieNotFoundError(AstrosError):
    def __init__(self, movie_id: str):
        super().__init__(f"Movie not found: {movie_id}")
        self.movie_id = movie_id


class InvalidCatalogError(AstrosError, ValueError):
    """The catalog file is unreadable or missing required columns."""


class StoreUnavailableError(AstrosError):
    """The document store cannot be reached."""


class StoreSchemaError(AstrosError):
    """An existing index was created with an incompatible schema."""


class EmbeddingModelMismatchError(AstrosError):
    """The embeddings file was produced by a different model than the configured one."""
