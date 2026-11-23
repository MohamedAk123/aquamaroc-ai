from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from services.api.app.db.base import Base, utc_now


class GeometryPoint(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw) -> str:
        return "geometry(POINT,4326)"


json_type = JSON().with_variant(JSONB(), "postgresql")


class Basin(Base):
    __tablename__ = "basins"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    code: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Reservoir(Base):
    __tablename__ = "reservoirs"
    __table_args__ = (
        UniqueConstraint("basin_id", "normalized_name"),
        CheckConstraint("capacity_mm3 IS NULL OR capacity_mm3 > 0", name="capacity_positive"),
        CheckConstraint("latitude IS NULL OR latitude BETWEEN -90 AND 90", name="latitude_range"),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180", name="longitude_range"
        ),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL AND geometry IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL AND coordinates_source IS NOT NULL)",
            name="coordinates_provenance",
        ),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    basin_id: Mapped[UUID] = mapped_column(ForeignKey("basins.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    normalized_name: Mapped[str] = mapped_column(String(200))
    capacity_mm3: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    capacity_source: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    geometry: Mapped[str | None] = mapped_column(Text().with_variant(GeometryPoint(), "postgresql"))
    coordinates_source: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class DataSource(Base):
    __tablename__ = "data_sources"
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('DEMO','VERIFIED','TO_VERIFY')",
            name="verification_status",
        ),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(300))
    producer: Mapped[str | None] = mapped_column(String(300))
    dataset_url: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(30))
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_status: Mapped[str] = mapped_column(String(20), default="TO_VERIFY")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (
        UniqueConstraint("source_id", "sha256", "is_demo"),
        CheckConstraint("status IN ('pending','success','partial','failed')", name="status"),
        CheckConstraint(
            "rows_read >= 0 AND rows_valid >= 0 AND rows_rejected >= 0 "
            "AND rows_read = rows_valid + rows_rejected",
            name="row_counts",
        ),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("data_sources.id"), index=True)
    filename: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    archive_path: Mapped[str] = mapped_column(Text)
    mapping_sha256: Mapped[str] = mapped_column(String(64))
    provenance: Mapped[dict] = mapped_column(json_type)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    rows_read: Mapped[int] = mapped_column(Integer, default=0)
    rows_valid: Mapped[int] = mapped_column(Integer, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean)


class Measurement(Base):
    __tablename__ = "reservoir_measurements"
    __table_args__ = (
        UniqueConstraint("reservoir_id", "observation_date", "source_id", "data_kind"),
        CheckConstraint("storage_mm3 IS NULL OR storage_mm3 >= 0", name="storage_nonnegative"),
        CheckConstraint(
            "filling_rate_pct IS NULL OR filling_rate_pct BETWEEN 0 AND 100",
            name="filling_range",
        ),
        CheckConstraint(
            "storage_mm3 IS NOT NULL OR filling_rate_pct IS NOT NULL",
            name="has_measurement",
        ),
        CheckConstraint("data_kind IN ('OFFICIAL','DEMO','UNVERIFIED')", name="data_kind"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    reservoir_id: Mapped[UUID] = mapped_column(ForeignKey("reservoirs.id"))
    source_id: Mapped[UUID] = mapped_column(ForeignKey("data_sources.id"), index=True)
    ingestion_run_id: Mapped[UUID] = mapped_column(ForeignKey("ingestion_runs.id"), index=True)
    observation_date: Mapped[date] = mapped_column(Date)
    storage_mm3: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    filling_rate_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 4))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    quality_status: Mapped[str] = mapped_column(String(30), default="VALID")
    data_kind: Mapped[str] = mapped_column(String(20))


Index(
    "ix_measurement_reservoir_date_desc",
    Measurement.reservoir_id,
    Measurement.observation_date.desc(),
)


class QualityIssue(Base):
    __tablename__ = "quality_issues"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    ingestion_run_id: Mapped[UUID] = mapped_column(ForeignKey("ingestion_runs.id"), index=True)
    measurement_id: Mapped[UUID | None] = mapped_column(ForeignKey("reservoir_measurements.id"))
    issue_type: Mapped[str] = mapped_column(String(60))
    severity: Mapped[str] = mapped_column(String(20))
    details: Mapped[dict] = mapped_column(json_type)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
