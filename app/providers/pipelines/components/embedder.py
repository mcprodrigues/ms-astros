"""
Embedder component for generating document embedding.
Uses sentence-transformers for multilingual semantic embeddings.
"""

import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class EmbedderComponent:
    """
    Embedder component for generating text embeddings.
    Implements singleton pattern to avoid loading model multiple times.
    """

    _instance: Optional["EmbedderComponent"] = None
    _model: Optional[SentenceTransformer] = None
    _model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbedderComponent, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._load_model()

    def _load_model(self) -> None:
        """
        Load the sentence-transformers model.
        Model is cached after first load for performance.
        """
        try:
            logger.info(f"Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def encode(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
          text: Input text to encode

        Returns:
          np.ndarray: Generated embedding vector
        """
        try:
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            raise

    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts in batch.
        More efficient than encoding one by one.

        Args:
          texts: List of input texts to encode
          batch_size: Size of batches for encoding

        Returns:
          List[np.ndarray]: List of generated embedding vectors
        """
        try:
            logger.info(
                f"Encoding batch of {len(texts)} texts with batch size {batch_size}"
            )
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 50,
            )
            logger.info("Batch encoding completed successfully")
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding batch of texts: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.

        Returns:
          int: Dimension of the embeddings
        """
        return self._model.get_sentence_embedding_dimension()
