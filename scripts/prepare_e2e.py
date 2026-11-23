"""Prépare une base de démonstration pour les tests Web ; aucun fichier officiel."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from pipelines.ingestion.demo import SOURCE_ID, seed_references
from pipelines.ingestion.import_xlsx import import_file
from services.api.app.core.config import get_settings
from services.api.app.db.session import get_engine


def main() -> None:
    if get_settings().app_mode != "demo":
        raise SystemExit("Les tests Web exigent APP_MODE=demo")
    command.upgrade(Config("alembic.ini"), "head")
    engine = get_engine()
    seed_references(engine)
    result = import_file(
        engine,
        Path("data/demo/reservoirs_demo.xlsx"),
        SOURCE_ID,
        Path("config/column_mapping.yaml"),
        "demo",
        Path(".cache/e2e-archive"),
    )
    if result.status != "success":
        raise SystemExit(f"Préparation DEMO échouée : {result.status}")
    print("Base DEMO des tests Web prête")


if __name__ == "__main__":
    main()
