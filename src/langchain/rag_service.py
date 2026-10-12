import os

from langfuse.langchain import CallbackHandler

from config.settings import settings
from src.langchain.rag_chain import RAGChain


class RAGService:
    """Единый интерфейс для работы с RAG."""

    def __init__(self) -> None:
        self.rag = RAGChain()

        self.langfuse_handler = None

        if (
            settings.langfuse_enabled
            and os.getenv("LANGFUSE_PUBLIC_KEY")
            and os.getenv("LANGFUSE_SECRET_KEY")
        ):
            self.langfuse_handler = CallbackHandler()

    def ask(
        self,
        question: str,
        session_id: str | None = None,
    ) -> str:
        """Отвечает на вопрос с использованием RAG."""

        config = {
            "run_name": "historical-rag",
            "metadata": {
                "retrieval": "hybrid_search",
                "model": settings.model_name,
            },
        }

        if session_id:
            config["metadata"]["langfuse_session_id"] = session_id

        if self.langfuse_handler is not None:
            config["callbacks"] = [self.langfuse_handler]

        return self.rag.invoke(question, config=config)

    def retrieve_context(self, question: str) -> str:
        """Возвращает контекст без генерации ответа."""

        return self.rag.retriever.retrieve(question)