from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.retrieval.hybrid_search import HybridRetriever


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    rank: int

    bm25_rank: int | None = None
    vector_rank: int | None = None


class RetrievalPipeline:

    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        chunks_engine: Engine,
        chunks_table: str = "chunks",
    ) -> None:
        self.hybrid_retriever = hybrid_retriever
        self.chunks_engine = chunks_engine
        self.chunks_table = chunks_table

    def retrieve(
        self,
        question: str,
        top_k: int = 10,
        candidate_k: int | None = None,
    ) -> list[RetrievedChunk]:

        # 1. BM25 + Vector + RRF
        results = self.hybrid_retriever.retrieve(
            query=question,
            top_k=top_k,
            candidate_k=candidate_k,
        )

        if not results:
            return []

        chunk_ids = [int(result.chunk_id) for result in results]

        # 2. Получаем тексты из отдельной БД
        sql = text(
            f"""
            SELECT
                id,
                chunk_text
            FROM {self.chunks_table}
            WHERE id = ANY(:chunk_ids)
            """
        )

        with self.chunks_engine.connect() as connection:
            rows = connection.execute(
                sql,
                {
                    "chunk_ids": chunk_ids,
                },
            ).fetchall()

        chunks_by_id = {
            str(row.id): row.chunk_text
            for row in rows
        }

        # 3. Восстанавливаем порядок RRF
        retrieved_chunks = []

        for result in results:

            chunk_text = chunks_by_id.get(result.chunk_id)

            if chunk_text is None:
                continue

            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=result.chunk_id,
                    text=chunk_text,
                    score=result.score,
                    rank=result.rank,
                    bm25_rank=result.bm25_rank,
                    vector_rank=result.vector_rank,
                )
            )

        return retrieved_chunks