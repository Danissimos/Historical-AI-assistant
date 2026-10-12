from __future__ import annotations

from sqlalchemy import text, event
from pgvector.psycopg2 import register_vector

from src.utils.db import get_engine


class EmbeddingsRepository:

    def __init__(self, env_path: str = "vector_db.env") -> None:
        self._engine = get_engine(env_path)

        @event.listens_for(self._engine, "connect")
        def connect(dbapi_connection, connection_record):
            register_vector(dbapi_connection)

    def insert_embeddings(
        self,
        rows: list[tuple[int, list[float]]],
    ) -> None:

        query = text("""
            INSERT INTO embeddings_store
                (chunk_id, embedding)
            VALUES
                (:chunk_id, :embedding)
            ON CONFLICT (chunk_id, embedding_model)
            DO NOTHING
        """)

        with self._engine.begin() as connection:
            connection.execute(
                query,
                [
                    {
                        "chunk_id": chunk_id,
                        "embedding": embedding,
                    }
                    for chunk_id, embedding in rows
                ],
            )