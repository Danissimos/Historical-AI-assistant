from __future__ import annotations
from typing import Iterable
import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    """
    Класс для формирования эмбеддингов текстов.
    """

    def __init__(
        self,
        model_name: str = "ai-sage/Giga-Embeddings-instruct",
        device: str = "cpu",
        normalize_embeddings: bool = True,
    ) -> None:
        self._model = SentenceTransformer(
            model_name_or_path=model_name,
            device=device,
            trust_remote_code=True,
        )
        self._normalize_embeddings = normalize_embeddings

    @property
    def embedding_dimension(self) -> int:
        """
        Размерность эмбеддингов модели.
        """
        return self._model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> np.ndarray:
        """
        Построение эмбеддинга одного текста.
        """
        embedding = self._model.encode(
            sentences=text,
            normalize_embeddings=self._normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return embedding

    def embed_batch(
        self,
        texts: Iterable[str],
        batch_size: int = 32,
    ) -> np.ndarray:
        """
        Построение эмбеддингов для списка текстов.
        """
        embeddings = self._model.encode(
            sentences=list(texts),
            batch_size=batch_size,
            normalize_embeddings=self._normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        return embeddings