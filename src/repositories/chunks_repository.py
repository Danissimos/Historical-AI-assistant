from __future__ import annotations

from sqlalchemy import text

from src.utils.db import get_engine


class ChunksRepository:

    def __init__(self, env_path: str = ".env") -> None:
        self._engine = get_engine(env_path)

    def get_chunks(
            self,
            start_chunk_id: int,
            limit: int,
    ) -> list[dict]:
        query = text("""
            SELECT
                id,
                chunk_text
            FROM chunks
            WHERE id >= :start_chunk_id
            ORDER BY id
            LIMIT :limit
        """)

        with self._engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "start_chunk_id": start_chunk_id,
                    "limit": limit,
                },
            )

            return [dict(row._mapping) for row in result]