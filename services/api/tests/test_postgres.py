"""Intégration réelle, isolée dans un schéma aléatoire d'une base de tests."""

import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pipelines.ingestion.demo import SOURCE_ID, seed_references
from pipelines.ingestion.import_xlsx import import_file
from services.api.app.core.config import Settings, get_settings
from services.api.app.db.session import get_session
from services.api.app.main import create_app
from services.api.app.models import Measurement


@pytest.fixture
def postgres_engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL absent : moteur PostgreSQL/PostGIS requis")
    if not url.startswith("postgresql"):
        pytest.fail("TEST_DATABASE_URL doit désigner une base PostgreSQL isolée")
    admin = create_engine(url)
    schema = f"test_{uuid4().hex}"
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema},public"})
    try:
        with admin.begin() as db:
            db.execute(text(f'CREATE SCHEMA "{schema}"'))
        with engine.connect() as db:
            config = Config("alembic.ini")
            config.attributes["connection"] = db
            command.upgrade(config, "head")
            db.commit()
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as db:
            db.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin.dispose()


@pytest.mark.postgres
def test_postgis_migration_and_real_ingestion(postgres_engine, tmp_path):
    engine = postgres_engine
    seed_references(engine)
    report = import_file(
        engine,
        Path("data/demo/reservoirs_demo.xlsx"),
        SOURCE_ID,
        Path("config/column_mapping.yaml"),
        "demo",
        tmp_path / "archive",
    )
    assert report.status == "success"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Measurement)) == 4
        assert db.scalar(text("SELECT PostGIS_Version()"))
        assert (
            db.scalar(
                text(
                    "SELECT data_type FROM information_schema.columns WHERE "
                    "table_schema=current_schema() AND table_name='quality_issues' "
                    "AND column_name='details'"
                )
            )
            == "jsonb"
        )
        with pytest.raises(IntegrityError):
            db.execute(text("UPDATE reservoir_measurements SET filling_rate_pct=101"))
            db.flush()
        db.rollback()
        assert db.scalar(select(func.count()).select_from(Measurement)) == 4

    app = create_app()

    def session():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_session] = session
    app.dependency_overrides[get_settings] = lambda: Settings(app_mode="demo")
    with TestClient(app) as client:
        assert client.get("/ready").status_code == 200
        assert client.get("/api/v1/reservoirs").json()["total"] == 2
