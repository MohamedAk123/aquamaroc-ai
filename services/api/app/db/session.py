from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session

from services.api.app.core.config import get_settings


def build_engine(url: str) -> Engine:
    options = {"check_same_thread": False} if url.startswith("sqlite") else {"connect_timeout": 3}
    engine = create_engine(url, pool_pre_ping=True, connect_args=options)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _record):
            connection.execute("PRAGMA foreign_keys=ON")

    return engine


@lru_cache
def get_engine() -> Engine:
    return build_engine(get_settings().database_url)


def get_session() -> Generator[Session]:
    with Session(get_engine()) as session:
        yield session
