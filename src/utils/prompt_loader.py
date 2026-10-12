from pathlib import Path

import yaml
from langchain_core.prompts import ChatPromptTemplate


def load_prompt(path: Path) -> ChatPromptTemplate:
    """Загружает промпт из YAML-файла."""

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return ChatPromptTemplate.from_messages(
        [
            ("system", data["system"]),
            ("human", data["human"]),
        ]
    )