import pytest

from app.providers.pipelines.components import store as store_module
from app.providers.pipelines.components.store import DocumentStoreProvider, StoreUnavailableError


def make_provider(attempts: int = 3) -> DocumentStoreProvider:
    return DocumentStoreProvider(
        url="http://weaviate.invalid:8080",
        index_name="Test",
        connect_attempts=attempts,
        backoff_seconds=0.01,
    )


def test_wait_until_ready_retries_until_store_answers(monkeypatch):
    provider = make_provider()
    answers = iter([False, False, True])
    monkeypatch.setattr(provider, "is_ready", lambda: next(answers))
    monkeypatch.setattr(store_module.time, "sleep", lambda _s: None)

    provider.wait_until_ready()  # does not raise


def test_wait_until_ready_raises_after_exhausting_attempts(monkeypatch):
    provider = make_provider(attempts=2)
    calls = []
    monkeypatch.setattr(provider, "is_ready", lambda: calls.append(1) or False)
    monkeypatch.setattr(store_module.time, "sleep", lambda _s: None)

    with pytest.raises(StoreUnavailableError):
        provider.wait_until_ready()
    assert len(calls) == 2


def test_is_ready_is_false_when_store_unreachable():
    assert make_provider().is_ready() is False
