"""Génère et référence uniquement des données synthétiques DEMO."""

from datetime import date
from pathlib import Path
from uuid import UUID

from openpyxl import Workbook
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from services.api.app.core.config import get_settings
from services.api.app.db.session import get_engine
from services.api.app.models import Basin, DataSource, Reservoir

SOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
BASIN_ID = UUID("00000000-0000-0000-0000-000000000010")
RESERVOIR_IDS = [UUID(f"00000000-0000-0000-0000-00000000010{i}") for i in (1, 2)]
DEMO_ROWS = [
    ["Réservoir synthétique Alpha", date(2026, 1, 1), "12,75", "25,5"],
    ["Réservoir synthétique Alpha", date(2026, 1, 2), "13,10", "26,2"],
    ["Réservoir synthétique Beta", date(2026, 1, 1), "8,25", "16,5"],
    ["Réservoir synthétique Beta", date(2026, 1, 2), "8,40", "16,8"],
]


def write_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    book = Workbook()
    sheet = book.active
    sheet.title = "Mesures_DEMO"
    sheet.append(["DEMO — Données synthétiques, aucun barrage réel"])
    sheet.append(["Barrage", "Date du relevé", "Réserve (Mm3)", "Remplissage (%)"])
    for row in DEMO_ROWS:
        sheet.append(row)
    book.save(path)
    book.close()


def seed_references(engine: Engine) -> None:
    with Session(engine) as db, db.begin():
        if db.get(Basin, BASIN_ID) is None:
            db.add(Basin(id=BASIN_ID, name="Bassin synthétique DEMO", code="DEMO"))
            db.flush()
        if db.get(DataSource, SOURCE_ID) is None:
            db.add(
                DataSource(
                    id=SOURCE_ID,
                    title="DEMO — Jeu synthétique AquaMaroc AI",
                    producer="Générateur local",
                    source_type="synthetic",
                    verification_status="DEMO",
                    license="Données synthétiques du projet",
                )
            )
        for reservoir_id, label in zip(RESERVOIR_IDS, ("Alpha", "Beta"), strict=True):
            if db.get(Reservoir, reservoir_id) is None:
                db.add(
                    Reservoir(
                        id=reservoir_id,
                        basin_id=BASIN_ID,
                        name=f"Réservoir synthétique {label}",
                        normalized_name=f"demo-{label.lower()}",
                    )
                )


def main() -> None:
    if get_settings().app_mode != "demo":
        raise SystemExit("La génération DEMO exige APP_MODE=demo")
    path = Path("data/demo/reservoirs_demo.xlsx")
    if not path.exists():
        write_fixture(path)
    seed_references(get_engine())
    print(f"DEMO créé ; source-id={SOURCE_ID}")


if __name__ == "__main__":
    main()
