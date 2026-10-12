from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass(slots=True)
class RetrievalResult:
    chunk_id: str
    score: float
    rank: int


class VectorRetriever:

    def __init__(
        self,
        engine: Engine,
        embedding_model,
        table_name: str = "embeddings_store",
    ) -> None:
        self.engine = engine
        self.embedding_model = embedding_model
        self.table_name = table_name

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[RetrievalResult]:

        if not query.strip():
            return []

        if top_k <= 0:
            return []

        query_embedding = self.embedding_model.encode(
            query,
            normalize_embeddings=True,
        )

        sql = text(
            f"""
            SELECT
                chunk_id,
                1 - (embedding <=> :embedding) AS score
            FROM {self.table_name}
            ORDER BY embedding <=> :embedding
            LIMIT :top_k
            """
        )

        with self.engine.connect() as connection:
            rows = connection.execute(
                sql,
                {
                    "embedding": query_embedding,
                    "top_k": top_k,
                },
            ).fetchall()

        return [
            RetrievalResult(
                chunk_id=str(row.chunk_id),
                score=float(row.score),
                rank=rank,
            )
            for rank, row in enumerate(rows, start=1)
        ]