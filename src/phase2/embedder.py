"""
Embedding using sentence-transformers. Used for indexing and query encoding.
"""
from __future__ import annotations

from typing import List, Union


def get_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """Return an embedder instance (lazy load model on first encode)."""
    return _Embedder(model_name)


class _Embedder:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None

    def _ensure_model(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)

    def encode(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Encode one or more texts to embedding vectors."""
        self._ensure_model()
        if isinstance(texts, str):
            texts = [texts]
        if not texts:
            return []
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
