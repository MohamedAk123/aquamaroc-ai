from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

DataKind = Literal["DEMO", "OFFICIAL", "UNVERIFIED"]


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
    mode: Literal["demo", "official"]
    is_real_time: bool = False


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BasinRead(ReadModel):
    id: UUID
    name: str
    code: str | None


class ReservoirRead(ReadModel):
    id: UUID
    basin_id: UUID
    name: str
    capacity_mm3: Decimal | None
    capacity_source: str | None = None
    latitude: Decimal | None
    longitude: Decimal | None
    coordinates_source: str | None


class MeasurementRead(ReadModel):
    id: UUID
    reservoir_id: UUID
    source_id: UUID
    ingestion_run_id: UUID
    observation_date: date
    storage_mm3: Decimal | None
    filling_rate_pct: Decimal | None
    published_at: datetime | None
    ingested_at: datetime
    quality_status: str
    data_kind: DataKind

    @field_serializer("published_at", "ingested_at")
    def iso_date(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        # SQLite retire le fuseau ; toutes les écritures de l'application sont UTC.
        from datetime import UTC

        return value.replace(tzinfo=value.tzinfo or UTC).isoformat()


class FreshnessRead(BaseModel):
    source_id: UUID
    title: str
    producer: str | None = None
    dataset_url: str | None
    license: str | None
    verification_status: str
    checked_at: datetime | None
    latest_observation_date: date | None
    latest_published_at: datetime | None
    latest_ingested_at: datetime | None
    latest_run_status: str | None
    latest_run_completed_at: datetime | None

    @field_serializer(
        "checked_at", "latest_published_at", "latest_ingested_at", "latest_run_completed_at"
    )
    def iso_date(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        from datetime import UTC

        return value.replace(tzinfo=value.tzinfo or UTC).isoformat()
