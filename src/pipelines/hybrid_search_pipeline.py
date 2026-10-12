from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from src.utils.db import get_engine, register_pgvector

from src.retrieval.sparse_retriever import BM25Retriever
from src.retrieval.dense_retriever import VectorRetriever
from src.retrieval.hybrid_search import HybridRetriever
from src.retrieval.hybrid_search_retrieval import RetrievalPipeline


class HybridSearchRetriever:
    """
    Высокоуровневый интерфейс для гибридного поиска
    по исторической базе знаний.
    """

    def __init__(
        self,
        top_k: int = 10,
        candidate_k: int = 30,
    ) -> None:
        self.top_k = top_k
        self.candidate_k = candidate_k

        # --------------------------------------------------------
        # Paths
        # --------------------------------------------------------

        base_dir = Path(__file__).resolve().parents[1]

        chunks_creds = (
            base_dir
            / "env"
            / ".env"
        )

        embeddings_creds = (
            base_dir
            / "env"
            / "vector_db.env"
        )

        # --------------------------------------------------------
        # Environment
        # --------------------------------------------------------

        load_dotenv(chunks_creds)

        hf_token = os.getenv("HF_TOKEN")

        # --------------------------------------------------------
        # Databases
        # --------------------------------------------------------

        chunks_engine = get_engine(
            chunks_creds
        )

        embeddings_engine = get_engine(
            embeddings_creds
        )

        register_pgvector(embeddings_engine)

        # --------------------------------------------------------
        # BM25
        # --------------------------------------------------------

        bm25 = BM25Retriever(
            engine=chunks_engine,
        )

        bm25.fit()

        # --------------------------------------------------------
        # Embedding model
        # --------------------------------------------------------

        embedding_model = SentenceTransformer(
            model_name_or_path="intfloat/multilingual-e5-base",
            device="cuda",
            trust_remote_code=True,
            token=hf_token,
        )

        # --------------------------------------------------------
        # Vector
        # --------------------------------------------------------

        vector = VectorRetriever(
            engine=embeddings_engine,
            embedding_model=embedding_model,
        )

        # --------------------------------------------------------
        # Hybrid
        # --------------------------------------------------------

        hybrid = HybridRetriever(
            bm25_retriever=bm25,
            vector_retriever=vector,
        )

        # --------------------------------------------------------
        # Pipeline
        # --------------------------------------------------------

        self.pipeline = RetrievalPipeline(
            hybrid_retriever=hybrid,
            chunks_engine=chunks_engine,
        )

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        candidate_k: int | None = None,
    ):
        """
        Выполнить гибридный поиск по базе знаний.
        """

        return self.pipeline.retrieve(
            question=question,
            top_k=top_k or self.top_k,
            candidate_k=candidate_k or self.candidate_k,
        )