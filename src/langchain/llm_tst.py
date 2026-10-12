from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_ollama import ChatOllama

from src.pipelines.hybrid_search_pipeline import HybridSearchRetriever


# ============================================================
# Конфигурация
# ============================================================

# Путь к корню проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Полный путь к .env
ENV_PATH = BASE_DIR / "env" / ".env"

# Загружаем переменные окружения
load_dotenv(dotenv_path=ENV_PATH, override=True)

MODEL_NAME = "qwen3:8b"

SYSTEM_PROMPT = """
Ты — ИИ-ассистент, отвечающий на вопросы на основании найденных документов.

Правила:
1. Отвечай только на основании предоставленного контекста.
2. Если контекст не содержит достаточной информации для ответа,
   напиши: "В предоставленном контексте недостаточно информации."
3. Не используй собственные знания для дополнения ответа.
4. Не делай предположений.
5. Если контекст содержит только часть информации,
   ответь на ту часть вопроса, для которой есть подтверждения.
"""


# ============================================================
# Langfuse
# ============================================================

langfuse_handler = CallbackHandler()


# ============================================================
# Retriever
# ============================================================

retriever = HybridSearchRetriever()


def retrieve_context(question: str) -> str:
    """Выполняет гибридный поиск и возвращает контекст."""
    return retriever.retrieve(question)


# ============================================================
# Prompt
# ============================================================

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    (
        "human",
        """Контекст:
{context}

Вопрос:
{question}
"""
    ),
])


# ============================================================
# LLM
# ============================================================

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0,
)


# ============================================================
# RAG chain
# ============================================================

chain = (
    {
        "context": RunnableLambda(
            lambda x: retrieve_context(x["question"])
        ),
        "question": RunnablePassthrough()
        | RunnableLambda(lambda x: x["question"]),
    }
    | prompt
    | llm
    | StrOutputParser()
)


# ============================================================
# Запуск
# ============================================================

if __name__ == "__main__":
    question = (
        "Расскажи мне подробнее про Вторую мировую войну. "
        "Что там было, что это вообще такое? "
    )

    response = chain.invoke(
        {"question": question},
        config={
            "callbacks": [langfuse_handler],
            "run_name": "historical-rag",
            "metadata": {
                "retrieval": "hybrid_search",
                "model": MODEL_NAME,
            },
        },
    )

    print(response)