from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from services.api.app.core.config import get_settings
from services.api.app.db.session import build_engine, get_engine


@pytest.fixture
def engine(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("APP_MODE", "demo")
    get_settings.cache_clear()
    get_engine.cache_clear()
    config = Config(str(Path(__file__).parent / "alembic.ini"))
    command.upgrade(config, "head")
    engine = build_engine(url)
    yield engine
    engine.dispose()
    get_engine.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def seeded(engine):
    from pipelines.ingestion.demo import seed_references

    seed_references(engine)
    return engine
