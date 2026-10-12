from pathlib import Path
from dotenv import dotenv_values

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from pgvector.psycopg2 import register_vector



def get_engine(env_path: Path) -> Engine:

    config = dotenv_values(env_path)

    return create_engine(
        f"postgresql+psycopg2://"
        f"{config['POSTGRES_USER']}:"
        f"{config['POSTGRES_PASSWORD']}@"
        f"{config['POSTGRES_HOST']}:"
        f"{config['POSTGRES_PORT']}/"
        f"{config['POSTGRES_DB']}",
        pool_pre_ping=True,
    )

def register_pgvector(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        register_vector(dbapi_connection)