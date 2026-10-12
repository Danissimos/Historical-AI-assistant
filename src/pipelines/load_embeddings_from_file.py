from __future__ import annotations

from pathlib import Path
import io

from psycopg2 import sql
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import dotenv_values
from pgvector.psycopg2 import register_vector
from sqlalchemy import event


# ============================================================
# Конфигурация
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
print(BASE_DIR)

VECTOR_DB_ENV = BASE_DIR / "src" / "env" / "vector_db.env"

CHUNKS_FILE = BASE_DIR / "data" / "prepared" / "dumps" / "chunks_dump.parquet"
EMBEDDINGS_FILE = BASE_DIR / "data" / "prepared" / "dumps" / "embeddings_0000.npy"

EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

BATCH_SIZE = 1_000

# ============================================================
# Подключение к PostgreSQL
# ============================================================

def get_engine(env_path: Path):

    config = dotenv_values(env_path)

    required = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
    ]

    missing = [
        key
        for key in required
        if not config.get(key)
    ]

    if missing:
        raise ValueError(
            f"Отсутствуют переменные в {env_path}: "
            f"{', '.join(missing)}"
        )

    engine = create_engine(
        "postgresql+psycopg2://"
        f"{config['POSTGRES_USER']}:"
        f"{config['POSTGRES_PASSWORD']}@"
        f"{config['POSTGRES_HOST']}:"
        f"{config['POSTGRES_PORT']}/"
        f"{config['POSTGRES_DB']}",
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        register_vector(dbapi_connection)

    return engine


# ============================================================
# Загрузка
# ============================================================

def main() -> None:

    print("Загрузка embeddings...")

    embeddings = np.load(
        EMBEDDINGS_FILE,
        mmap_mode="r",
    )

    print(
        f"Embeddings shape: {embeddings.shape}"
    )

    print("Загрузка chunks...")

    chunks = pd.read_parquet(
        CHUNKS_FILE,
        columns=["id"],
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    # --------------------------------------------------------
    # Проверки
    # --------------------------------------------------------

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Количество чанков и embeddings "
            "не совпадает: "
            f"{len(chunks)} != {len(embeddings)}"
        )

    if embeddings.ndim != 2:
        raise ValueError(
            f"Ожидался двумерный массив embeddings, "
            f"получено: {embeddings.shape}"
        )

    if embeddings.shape[1] != 768:
        raise ValueError(
            f"Ожидалась размерность 768, "
            f"получено: {embeddings.shape[1]}"
        )

    # --------------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------------

    engine = get_engine(
        VECTOR_DB_ENV
    )

    total = len(chunks)

    print(f"\nНачинаем загрузку {total} embeddings...")

    chunk_ids = chunks["id"].to_numpy()

    raw_connection = engine.raw_connection()

    try:
        cursor = raw_connection.cursor()

        buffer = io.StringIO()

        for start in range(0, total, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total)

            buffer.seek(0)
            buffer.truncate(0)

            for i in range(start, end):
                vector = ",".join(
                    str(float(value))
                    for value in embeddings[i]
                )

                buffer.write(
                    f"{int(chunk_ids[i])}\t"
                    f"{EMBEDDING_MODEL}\t"
                    f"[{vector}]\n"
                )

            buffer.seek(0)

            cursor.copy_expert(
                """
                COPY embeddings_store
                (
                    chunk_id,
                    embedding_model,
                    embedding
                )
                FROM STDIN
                WITH (
                    FORMAT text,
                    DELIMITER E'\\t'
                )
                """,
                buffer,
            )

            print(f"Обработано: {end}/{total}")

        raw_connection.commit()

    finally:
        raw_connection.close()

    print("\nГотово.")
    print(f"Обработано: {total}")


if __name__ == "__main__":
    main()