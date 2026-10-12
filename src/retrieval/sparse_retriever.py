from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from rank_bm25 import BM25Okapi
from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass(slots=True)
class RetrievalResult:
    chunk_id: str
    score: float
    rank: int


class BM25Retriever:
    """
    Lexical retriever на базе BM25.

    Индекс хранится в памяти.
    Данные для построения индекса загружаются из PostgreSQL.
    """

    def __init__(
        self,
        engine: Engine,
        table_name: str = "chunks",
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.engine = engine
        self.table_name = table_name

        self.k1 = k1
        self.b = b

        self._bm25: BM25Okapi | None = None
        self._chunk_ids: list[str] = []

    def fit(self) -> None:
        """
        Загрузить chunks из PostgreSQL и построить BM25-индекс.
        """

        sql = text(
            f"""
            SELECT
                id,
                chunk_text
            FROM {self.table_name}
            ORDER BY id
            """
        )

        with self.engine.connect() as connection:
            rows = connection.execute(sql).fetchall()

        if not rows:
            raise ValueError(
                f"No chunks found in table '{self.table_name}'."
            )

        self._chunk_ids = [
            str(row.id)
            for row in rows
        ]

        tokenized_corpus = [
            self._tokenize(row.chunk_text)
            for row in rows
        ]

        self._bm25 = BM25Okapi(
            tokenized_corpus,
            k1=self.k1,
            b=self.b,
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[RetrievalResult]:

        if self._bm25 is None:
            raise RuntimeError(
                "BM25Retriever is not fitted. "
                "Call fit() first."
            )

        if not query.strip():
            return []

        if top_k <= 0:
            return []

        query_tokens = self._tokenize(query)

        scores = self._bm25.get_scores(query_tokens)

        top_indices = np.argsort(scores)[::-1][:top_k]

        return [
            RetrievalResult(
                chunk_id=self._chunk_ids[index],
                score=float(scores[index]),
                rank=rank,
            )
            for rank, index in enumerate(top_indices, start=1)
        ]

    @staticmethod
    def _tokenize(text_value: str) -> list[str]:
        return text_value.lower().split()