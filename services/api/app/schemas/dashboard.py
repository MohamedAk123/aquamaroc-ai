from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from services.api.app.schemas.read import MeasurementRead, ReservoirRead


class SnapshotRead(BaseModel):
    reservoir: ReservoirRead
    basin_name: str
    latest_date: date
    latest: MeasurementRead | None
    source_count: int


class OverviewRead(BaseModel):
    mode: Literal["demo", "official"]
    is_real_time: bool = False
    reservoirs: list[SnapshotRead]
    reservoir_count: int
    latest_observation_date: date | None
    storage_mm3: Decimal | None
    weighted_filling_rate_pct: Decimal | None
    comparable_count: int
    storage_status: str
    filling_status: str


class QualityRead(BaseModel):
    mode: Literal["demo", "official"]
    files_ingested: int
    observations: int
    rejected_rows: int
    rows_read: int
    missing_storage: int
    missing_filling_rate: int
    unresolved_issues: int


class ImportRead(BaseModel):
    id: UUID
    filename: str
    sha256: str
    source_id: UUID
    source_title: str
    source_checked_at: datetime | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    rows_read: int
    rows_valid: int
    rows_rejected: int


class IssueRead(BaseModel):
    id: UUID
    ingestion_run_id: UUID
    filename: str
    issue_type: str
    severity: str
    resolved_at: datetime | None
    row: int | None
    reason: str | None


class CoverageRead(BaseModel):
    reservoir_id: UUID
    reservoir_name: str
    source_id: UUID
    source_title: str
    data_kind: Literal["DEMO", "OFFICIAL", "UNVERIFIED"]
    first_date: date
    last_date: date
    observed_days: int
    span_days: int
    gap_days: int
