from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama

from config.settings import settings
from src.pipelines.hybrid_search_pipeline import HybridSearchRetriever
from src.utils.prompt_loader import load_prompt


class RAGChain:
    """Создаёт RAG-цепочку на основе гибридного поиска."""

    def __init__(self) -> None:
        self.retriever = HybridSearchRetriever()

        prompt_path = (
            settings.prompts_dir / "system_prompt.yaml"
        )
        prompt = load_prompt(prompt_path)

        llm = ChatOllama(
            model=settings.model_name,
            temperature=settings.temperature,
        )

        self.chain = (
            {
                "context": RunnableLambda(
                    lambda data: self.retriever.retrieve(
                        data["question"]
                    )
                ),
                "question": RunnableLambda(
                    lambda data: data["question"]
                ),
            }
            | prompt
            | llm
            | StrOutputParser()
        )

    def invoke(self, question: str, config: dict | None = None) -> str:
        """Выполняет поиск и генерирует ответ."""

        return self.chain.invoke(
            {"question": question},
            config=config,
        )