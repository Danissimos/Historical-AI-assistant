from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.langchain.rag_service import RAGService


app = FastAPI(title="Historical RAG API")

# Один экземпляр сервиса на всё приложение
rag = RAGService()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid4())

    try:
        answer = rag.ask(
            question=request.question,
            session_id=session_id,
        )
        return ChatResponse(
            answer=answer,
            session_id=session_id,
        )

    except Exception as exc:
        # Подробности ошибки лучше записывать в лог,
        # а клиенту возвращать общее сообщение.
        raise HTTPException(
            status_code=500,
            detail="Не удалось обработать запрос.",
        ) from exc


class RetrievalRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)


class RetrievalResponse(BaseModel):
    context: str


@app.post("/debug/retrieve", response_model=RetrievalResponse)
def debug_retrieve(request: RetrievalRequest) -> RetrievalResponse:
    try:
        context = rag.retrieve_context(request.question)
        return RetrievalResponse(context=context)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Не удалось выполнить поиск.",
        ) from exc