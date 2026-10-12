import uuid

import streamlit as st

from src.langchain.rag_service import RAGService


# ============================================================
# Настройки страницы
# ============================================================

st.set_page_config(
    page_title="Исторический ассистент",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# Инициализация состояния
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "rag_service" not in st.session_state:
    st.session_state.rag_service = None


@st.cache_resource
def get_rag_service():
    """Создаёт единый экземпляр RAG-сервиса."""
    return RAGService()


# ============================================================
# Оформление
# ============================================================

st.markdown(
    """
    <style>
        .block-container {
            max-width: 850px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            text-align: center;
            padding: 2rem 0 1.5rem 0;
        }

        .hero-icon {
            font-size: 3rem;
        }

        .hero h1 {
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: -1px;
            margin-bottom: 0.5rem;
        }

        .hero p {
            opacity: 0.7;
            font-size: 1.05rem;
        }

        [data-testid="stChatMessage"] {
            border-radius: 16px;
            padding: 1rem;
        }

        .disclaimer {
            text-align: center;
            font-size: 0.8rem;
            opacity: 0.6;
            padding-top: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Заголовок
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-icon">📚</div>
        <h1>Исторический ассистент</h1>
        <p>Исследуйте прошлое, задавайте вопросы и находите ответы.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Примеры вопросов
# ============================================================

if not st.session_state.messages:
    st.markdown("##### С чего начнём?")

    examples = [
        "Почему началась Вторая мировая война?",
        "Как проходила битва при Нарве в 1700 году?",
        "Какие события изменили ход истории России?",
        "Расскажи о ключевых исторических личностях.",
    ]

    columns = st.columns(2)

    for index, example in enumerate(examples):
        with columns[index % 2]:
            if st.button(
                example,
                key=f"example_{index}",
                use_container_width=True,
            ):
                st.session_state.pending_question = example
                st.rerun()


# ============================================================
# История сообщений
# ============================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# Ввод вопроса
# ============================================================

question = st.chat_input("Задайте вопрос об истории...")

if not question:
    question = st.session_state.pop("pending_question", None)


# ============================================================
# Обработка запроса
# ============================================================

if question:
    question = question.strip()

    if question:
        st.session_state.messages.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                with st.spinner(
                    "Ищу информацию и готовлю ответ..."
                ):
                    rag = get_rag_service()

                    answer = rag.ask(
                        question=question,
                        session_id=st.session_state.session_id,
                    )

                st.markdown(answer)

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception:
                st.error(
                    "Не удалось получить ответ. "
                    "Проверьте подключение к модели и доступность базы знаний."
                )

                # Подробности остаются в терминале, а не в UI.
                import logging
                logging.exception("Ошибка при обработке RAG-запроса")

        st.rerun()


# ============================================================
# Нижняя панель
# ============================================================

st.divider()

left, right = st.columns([1, 1])

with left:
    if st.button("＋ Новый диалог", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

with right:
    st.caption("Исторический ИИ-ассистент · Локальная модель")

st.markdown(
    """
    <div class="disclaimer">
        Ответы формируются на основе найденных документов и могут быть неполными.
    </div>
    """,
    unsafe_allow_html=True,
)