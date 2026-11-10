import logging
import time

from haystack_integrations.document_stores.weaviate import WeaviateDocumentStore
from haystack_integrations.document_stores.weaviate.document_store import (
    DOCUMENT_COLLECTION_PROPERTIES,
)
from weaviate.config import AdditionalConfig, Timeout
from weaviate.util import generate_uuid5

from app.domain.errors import StoreSchemaError, StoreUnavailableError
from app.providers.pipelines.interfaces import IDocumentStoreProvider

logger = logging.getLogger(__name__)

SEARCHABLE_TEXT_PROPERTIES = ("titulo", "sinopse", "descricao", "palavras_chave", "diretor")


def collection_properties() -> list[dict]:
    """
    Haystack's own properties (`_original_id`, `content`, `score`, ...) plus the
    movie fields. Declaring all of them explicitly prevents Weaviate's
    auto-schema from guessing types, e.g. typing UUID-shaped IDs as `uuid`.
    """
    own = [
        {"name": name, "dataType": ["text"], "indexSearchable": True}
        for name in SEARCHABLE_TEXT_PROPERTIES
    ]
    return [dict(prop) for prop in DOCUMENT_COLLECTION_PROPERTIES] + own


class DocumentStoreProvider(IDocumentStoreProvider):
    """Owns a single WeaviateDocumentStore connection."""

    def __init__(
        self,
        url: str,
        index_name: str,
        grpc_port: int = 50051,
        connect_attempts: int = 10,
        backoff_seconds: float = 1.0,
        query_timeout_seconds: float = 10.0,
        insert_timeout_seconds: float = 60.0,
    ):
        self._url = url
        self._index_name = index_name
        self._connect_attempts = connect_attempts
        self._backoff_seconds = backoff_seconds
        self._document_store = WeaviateDocumentStore(
            url=url,
            grpc_port=grpc_port,
            additional_config=AdditionalConfig(
                timeout=Timeout(init=5, query=query_timeout_seconds, insert=insert_timeout_seconds)
            ),
            collection_settings={
                "class": index_name,
                "vectorizer": "none",
                "properties": collection_properties(),
            },
        )

    def get_document_store(self) -> WeaviateDocumentStore:
        return self._document_store

    def is_ready(self) -> bool:
        try:
            return bool(self._document_store.client.is_ready())
        except Exception as e:
            logger.warning("Weaviate readiness check failed: %s", e)
            return False

    def reset(self) -> None:
        # Drop and recreate: faster than deleting in batches, and re-applies the schema.
        self._document_store.delete_all_documents(recreate_index=True)

    def ensure_compatible_schema(self) -> None:
        expected = {p["name"]: p["dataType"][0] for p in collection_properties()}
        actual = {
            p.name: p.data_type.value
            for p in self._document_store.collection.config.get().properties
        }
        wrong = {
            name: (actual[name], expected[name])
            for name in expected
            if name in actual and actual[name] != expected[name]
        }
        if wrong:
            details = ", ".join(f"{n} is {a}, expected {e}" for n, (a, e) in wrong.items())
            raise StoreSchemaError(
                f"Weaviate collection {self._index_name!r} has an incompatible schema "
                f"({details}). It cannot be fixed in place: drop it with "
                f"`curl -X DELETE {self._url}/v1/schema/{self._index_name}` and restart; "
                "the index is reseeded from the precomputed embeddings."
            )

    def document_exists(self, doc_id: str) -> bool:
        # The Weaviate store keys objects by uuid5 of the Haystack document id.
        return self._document_store.collection.data.exists(generate_uuid5(doc_id))

    def wait_until_ready(self) -> None:
        delay = self._backoff_seconds
        for attempt in range(1, self._connect_attempts + 1):
            if self.is_ready():
                logger.info("Connected to Weaviate at %s", self._url)
                return
            if attempt < self._connect_attempts:
                logger.info(
                    "Weaviate not ready (attempt %d/%d); retrying in %.1fs",
                    attempt,
                    self._connect_attempts,
                    delay,
                )
                time.sleep(delay)
                delay = min(delay * 2, 30.0)
        raise StoreUnavailableError(
            f"Weaviate at {self._url} not ready after {self._connect_attempts} attempts"
        )

    def close(self) -> None:
        try:
            self._document_store.close()
        except Exception as e:
            logger.warning("Error closing Weaviate connection: %s", e)
