import os

import pytest
from haystack_integrations.document_stores.weaviate import WeaviateDocumentStore

pytestmark = pytest.mark.integration


def test_document_store_connects_and_counts():
    store = WeaviateDocumentStore(
        url=os.getenv("WEAVIATE_URL", "http://localhost:8080"),
        collection_settings={"class": "AstrosCiSmoke", "vectorizer": "none"},
    )
    try:
        assert store.count_documents() >= 0
    finally:
        store.client.collections.delete("AstrosCiSmoke")
        store.close()
