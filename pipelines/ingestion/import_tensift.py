"""Import des trois éditions Tensift 2026 auditées, depuis leur dossier brut."""

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid5

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from pipelines.ingestion.import_xlsx import import_file
from pipelines.ingestion.tensift import (
    BASIN_ID,
    CAPACITIES,
    TensiftMapping,
    parse_tensift,
    reservoir_id,
)
from services.api.app.core.config import get_settings
from services.api.app.db.base import utc_now
from services.api.app.db.session import get_engine
from services.api.app.models import Basin, DataSource, Reservoir

DATASET = (
    "https://www.data.gov.ma/data/dataset/"
    "situation-journaliere-des-barrages-dans-le-bassin-du-tensift"
)
PRODUCER = "Agence du bassin hydraulique de Tensift"
SOURCE_ID = uuid5(BASIN_ID, DATASET)
EDITIONS = (
    (
        8,
        "aout",
        "Août_2026",
        3,
        "0b69e96f-6c95-40ff-8c91-3721984b2613",
        "818c761003cc96ba0bf0fd3da076089f956020ac09905de97b2dbefef54358d7",
    ),
    (
        9,
        "sept",
        "Sept_2026",
        3,
        "57580e59-8b9c-4bde-bf9f-2a25107bbf6e",
        "54195396f6358913416770b8dc2e90f1976d806186e50a96c75ca7fd6721eb46",
    ),
    (
        10,
        "oct",
        "Oct_2026",
        4,
        "aae7d44c-6170-45cf-a21a-9a6fde498c3a",
        "ff63f27e3b8e8b82073bdf424bf355754c694230c61d4db3b0d013e19a643c3d",
    ),
)


def validate_editions(directory: Path) -> list[tuple[Path, TensiftMapping]]:
    editions = []
    for month, label, sheet, header, resource, digest in EDITIONS:
        filename = f"data_barrages_tensift_{label}_2026.xlsx"
        file = directory / filename
        if not 0 < file.stat().st_size <= 10_000_000:
            raise ValueError(f"Fichier vide ou trop volumineux : {filename}")
        content = file.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError(f"Empreinte différente du classeur audité : {filename}")
        mapping = TensiftMapping(
            period=date(2026, month, 1),
            sheet=sheet,
            header_row=header,
            sha256=digest,
            resource_url=(
                "https://data.gov.ma/data/fr/dataset/0aff0dd1-3c7e-4e14-9cbf-18782902a6e4/"
                f"resource/{resource}/download/{filename}"
            ),
        )
        result = parse_tensift(content, mapping)
        if result.error:
            raise ValueError(f"{filename} : {result.error}")
        editions.append((file, mapping))
    return editions


def seed_catalog(engine: Engine) -> None:
    with Session(engine) as db, db.begin():
        if db.get(Basin, BASIN_ID) is None:
            db.add(Basin(id=BASIN_ID, name="Bassin du Tensift"))
            db.flush()
        source = db.get(DataSource, SOURCE_ID)
        if source is None:
            db.add(
                DataSource(
                    id=SOURCE_ID,
                    title="Situation journalière des barrages dans le bassin du Tensift",
                    producer=PRODUCER,
                    dataset_url=DATASET,
                    license="ODbL",
                    source_type="XLSX",
                    checked_at=utc_now(),
                    verification_status="VERIFIED",
                )
            )
        elif (source.dataset_url, source.verification_status) != (DATASET, "VERIFIED"):
            raise ValueError("Référentiel source incompatible")
        for name, capacity in CAPACITIES.items():
            identifier = reservoir_id(name)
            existing = db.get(Reservoir, identifier)
            if existing is None:
                db.add(
                    Reservoir(
                        id=identifier,
                        basin_id=BASIN_ID,
                        name=name,
                        normalized_name=name.casefold(),
                        capacity_mm3=Decimal(capacity),
                        capacity_source=DATASET,
                    )
                )
            elif (
                existing.basin_id,
                existing.name,
                existing.capacity_mm3,
                existing.capacity_source,
            ) != (BASIN_ID, name, Decimal(capacity), DATASET):
                raise ValueError(f"Référentiel existant incompatible : {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("data/raw/tensift"))
    args = parser.parse_args()
    settings = get_settings()
    if settings.app_mode != "official":
        parser.error("APP_MODE=official est requis")
    editions = validate_editions(args.directory)
    engine = get_engine()
    seed_catalog(engine)
    reports = [
        import_file(engine, file, SOURCE_ID, mapping, "official", settings.raw_archive_dir)
        for file, mapping in editions
    ]
    print(json.dumps([asdict(report) for report in reports], ensure_ascii=False))
    return 0 if all(report.status == "success" for report in reports) else 2


if __name__ == "__main__":
    raise SystemExit(main())
