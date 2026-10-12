from sqlalchemy import text
from src.utils.db import get_engine
from pathlib import Path


env_path = Path(__file__).resolve().parents[2] / "src/env/.env_graph_db"
GRAPH_NAME = "wiki_graph"


def init_age():
    engine = get_engine(
        env_path
    )

    with engine.connect() as conn:

        # Загружаем AGE
        conn.execute(
            text(
                """
                LOAD 'age';
                """
            )
        )

        # Для удобства работы с cypher
        conn.execute(
            text(
                """
                SET search_path = ag_catalog, "$user", public;
                """
            )
        )

        # Создаем граф
        conn.execute(
            text(
                f"""
                SELECT create_graph('{GRAPH_NAME}');
                """
            )
        )

    print(
        f"Apache AGE graph '{GRAPH_NAME}' initialized"
    )


if __name__ == "__main__":
    init_age()