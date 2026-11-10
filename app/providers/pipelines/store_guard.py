from collections.abc import Callable

from app.domain.errors import StoreUnavailableError
from app.providers.pipelines.interfaces import IDocumentStoreProvider


def call_store[T](provider: IDocumentStoreProvider, operation: Callable[[], T]) -> T:
    """
    Run a store operation, translating failures caused by an unreachable store
    into StoreUnavailableError. Other errors propagate unchanged.
    """
    try:
        return operation()
    except Exception as e:
        if not provider.is_ready():
            raise StoreUnavailableError("Document store is unavailable") from e
        raise
