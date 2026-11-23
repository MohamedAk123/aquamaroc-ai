"""Lecture d’un résultat ML hors ligne lié à un instantané officiel."""

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, FiniteFloat, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.api.app.models import DataSource, IngestionRun, Measurement, Reservoir

REPORT = Path(__file__).resolve().parents[1] / "resources" / "variation_review.json"


class Finding(BaseModel):
    reservoir_id: UUID
    reservoir_name: str
    observation_date: date
    storage_mm3: str
    delta_1d_mm3: str
    delta_7d_mm3: str
    source_id: UUID
    file_sha256: str
    score: FiniteFloat
    threshold: FiniteFloat


class VariationReport(BaseModel):
    schema_version: Literal[1]
    study_sha256: str
    model: Literal["Isolation Forest"]
    sklearn_version: str
    reference_start: date
    reference_end: date
    analysed_start: date
    analysed_end: date
    input_observations: int
    reference_samples: int
    analysed_samples: int
    findings: list[Finding]


class VariationReview(BaseModel):
    status: Literal["available", "unavailable"]
    mode: Literal["demo", "official"]
    report: VariationReport | None = None


def official_snapshot(db: Session) -> list[dict]:
    query = (
        select(Measurement, Reservoir.name, IngestionRun.sha256)
        .join(Reservoir, Measurement.reservoir_id == Reservoir.id)
        .join(IngestionRun, Measurement.ingestion_run_id == IngestionRun.id)
        .join(DataSource, Measurement.source_id == DataSource.id)
        .where(
            Measurement.data_kind == "OFFICIAL",
            DataSource.verification_status == "VERIFIED",
            IngestionRun.is_demo.is_(False),
        )
        .order_by(Measurement.reservoir_id, Measurement.source_id, Measurement.observation_date)
    )
    return [
        {
            "reservoir_id": str(row.reservoir_id),
            "reservoir_name": name,
            "source_id": str(row.source_id),
            "observation_date": row.observation_date.isoformat(),
            "storage_mm3": str(row.storage_mm3) if row.storage_mm3 is not None else None,
            "file_sha256": checksum,
        }
        for row, name, checksum in db.execute(query)
    ]


def snapshot_hash(rows: list[dict]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def read_variation_review(db: Session, mode: Literal["demo", "official"]) -> VariationReview:
    unavailable = VariationReview(status="unavailable", mode=mode)
    if mode != "official":
        return unavailable
    try:
        report = VariationReport.model_validate_json(REPORT.read_bytes())
    except (OSError, ValidationError):
        return unavailable
    if report.study_sha256 != snapshot_hash(official_snapshot(db)):
        return unavailable
    return VariationReview(status="available", mode=mode, report=report)
