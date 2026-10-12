from __future__ import annotations

from dataclasses import dataclass

from .sparse_retriever import BM25Retriever, RetrievalResult
from .dense_retriever import VectorRetriever


@dataclass(slots=True)
class HybridResult:
    """
    Результат hybrid search.

    Attributes:
        chunk_id: ID чанка.
        score: Итоговый RRF score.
        rank: Итоговая позиция.
        bm25_rank: Позиция в BM25 выдаче.
        vector_rank: Позиция в vector выдаче.
    """

    chunk_id: str
    score: float
    rank: int

    bm25_rank: int | None = None
    vector_rank: int | None = None


class HybridRetriever:
    """
    Hybrid retriever, объединяющий BM25 и vector search
    через Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        bm25_retriever: BM25Retriever,
        vector_retriever: VectorRetriever,
        rrf_k: int = 60,
    ) -> None:
        self.bm25_retriever = bm25_retriever
        self.vector_retriever = vector_retriever
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int | None = None,
    ) -> list[HybridResult]:
        """
        Выполнить hybrid search.

        Args:
            query:
                Поисковый запрос.

            top_k:
                Количество результатов, возвращаемых пользователю.

            candidate_k:
                Количество кандидатов, получаемых от каждого
                retriever'а до применения RRF.

                Если None, используется top_k.

        Returns:
            Результаты, отсортированные по RRF score.
        """

        if not query.strip():
            return []

        if top_k <= 0:
            return []

        if candidate_k is None:
            candidate_k = top_k

        if candidate_k <= 0:
            return []

        # --------------------------------------------------
        # 1. Получаем результаты от BM25
        # --------------------------------------------------

        bm25_results = self.bm25_retriever.retrieve(
            query=query,
            top_k=candidate_k,
        )

        # --------------------------------------------------
        # 2. Получаем результаты от Vector Search
        # --------------------------------------------------

        vector_results = self.vector_retriever.retrieve(
            query=query,
            top_k=candidate_k,
        )

        # --------------------------------------------------
        # 3. RRF
        # --------------------------------------------------

        rrf_scores: dict[str, float] = {}

        bm25_ranks: dict[str, int] = {}
        vector_ranks: dict[str, int] = {}

        for result in bm25_results:
            chunk_id = result.chunk_id

            bm25_ranks[chunk_id] = result.rank

            rrf_scores[chunk_id] = (
                rrf_scores.get(chunk_id, 0.0)
                + self._rrf_score(result.rank)
            )

        for result in vector_results:
            chunk_id = result.chunk_id

            vector_ranks[chunk_id] = result.rank

            rrf_scores[chunk_id] = (
                rrf_scores.get(chunk_id, 0.0)
                + self._rrf_score(result.rank)
            )

        # --------------------------------------------------
        # 4. Сортировка
        # --------------------------------------------------

        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        # --------------------------------------------------
        # 5. Формируем итоговую выдачу
        # --------------------------------------------------

        results: list[HybridResult] = []

        for rank, (chunk_id, score) in enumerate(
            sorted_results[:top_k],
            start=1,
        ):
            results.append(
                HybridResult(
                    chunk_id=chunk_id,
                    score=score,
                    rank=rank,
                    bm25_rank=bm25_ranks.get(chunk_id),
                    vector_rank=vector_ranks.get(chunk_id),
                )
            )

        return results

    def _rrf_score(self, rank: int) -> float:
        """
        Reciprocal Rank Fusion.

        RRF(d) = 1 / (k + rank)
        """

        return 1.0 / (self.rrf_k + rank)

