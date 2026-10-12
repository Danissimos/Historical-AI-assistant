from src.langchain.rag_service import RAGService


def main() -> None:
    rag = RAGService()

    print("RAG-ассистент запущен.")
    print("Для выхода введи 'exit'.\n")

    while True:
        question = input("Ты: ").strip()

        if question.lower() in {"exit", "quit", "выход"}:
            break

        if not question:
            continue

        try:
            response = rag.ask(question)
            print(f"\nАссистент: {response}\n")

        except Exception as exc:
            print(f"\nОшибка при обработке запроса: {exc}\n")


if __name__ == "__main__":
    main()