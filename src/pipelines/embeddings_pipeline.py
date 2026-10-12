from __future__ import annotations
from pathlib import Path
import os
from dotenv import load_dotenv

from src.embeddings.embedder import Embedder
from src.embeddings.repository import EmbeddingsRepository
from src.repositories.chunks_repository import ChunksRepository


class EmbeddingsPipeline:

    def __init__(
        self,
        chunks_env_path: str = ".env",
        vector_env_path: str = "vector_db.env",
        model_name: str = "ai-sage/Giga-Embeddings-instruct",
        device: str = "cuda",
    ) -> None:

        self._chunks_repository = ChunksRepository(
            env_path=chunks_env_path
        )

        self._embeddings_repository = EmbeddingsRepository(
            env_path=vector_env_path
        )

        self._embedder = Embedder(
            model_name=model_name,
            device=device,
        )

    def run(
        self,
        start_chunk_id: int,
        limit: int = 1000,
        batch_size: int = 64,
    ) -> None:
        """
        Формирование эмбеддингов и сохранение их в PostgreSQL.
        """

        chunks = self._chunks_repository.get_chunks(
            start_chunk_id=start_chunk_id,
            limit=limit,
        )

        if not chunks:
            print("Нет чанков для обработки.")
            return

        texts = [chunk["chunk_text"] for chunk in chunks]

        embeddings = self._embedder.embed_batch(
            texts=texts,
            batch_size=batch_size,
        )

        rows = [
            (
                chunk["id"],
                embedding.tolist(),
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        self._embeddings_repository.insert_embeddings(rows)

        print(f"Сохранено {len(rows)} эмбеддингов.")


CHUNKS_CREDS = Path(__file__).resolve().parents[1] / "env" / ".env"
EMBEDDINGS_CREDS = Path(__file__).resolve().parents[1] / "env" / "vector_db.env"

load_dotenv(CHUNKS_CREDS)
hf_token = os.getenv("HF_TOKEN")

pipeline = EmbeddingsPipeline(
    chunks_env_path=str(CHUNKS_CREDS),
    vector_env_path=str(EMBEDDINGS_CREDS),
    device="cpu",
)

pipeline.run(
    start_chunk_id=1,
    limit=1000,
)