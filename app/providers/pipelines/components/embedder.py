"""Sentence-transformers embedder."""

import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from app.providers.pipelines.interfaces import IEmbedder

logger = logging.getLogger(__name__)


class EmbedderComponent(IEmbedder):
    """
    Wraps a SentenceTransformer model. The model is loaded once, in the
    constructor, so a misconfigured model fails at startup rather than on
    the first request.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        logger.info("Loading embedding model: %s", model_name)
        self._model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded (dim=%d)", self.get_embedding_dimension())

    def encode(self, text: str) -> np.ndarray:
        return self._model.encode(text, convert_to_numpy=True)

    def encode_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        logger.info("Encoding batch of %d texts", len(texts))
        return self._model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 50,
        )

    def get_embedding_dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()
