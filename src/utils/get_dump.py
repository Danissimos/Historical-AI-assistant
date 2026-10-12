import pandas as pd
from pathlib import Path
from sqlalchemy import text
from src.utils.db import get_engine


CHUNKS_CREDS = Path(__file__).resolve().parents[1] / "env" / ".env"
CHUNK_DUMP = Path(__file__).resolve().parents[2] / "data" / "prepared" / "dumps" / "chunks_dump.parquet"

engine = get_engine(CHUNKS_CREDS)

query = text("""
    SELECT
        id,
        chunk_text
    FROM chunks
    ORDER BY id
""")

with engine.connect() as connection:
    df = pd.read_sql(query, connection)

df.to_parquet(
    str(CHUNK_DUMP),
    index=False,
)