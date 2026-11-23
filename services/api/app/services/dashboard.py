from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from services.api.app.models import Basin, IngestionRun, Measurement, QualityIssue, Reservoir
from services.api.app.repositories.catalog import allowed_kinds


def overview(
    db: Session,
    mode: str,
    basin_id: UUID | None = None,
    search: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    data_kind: str | None = None,
    source_id: UUID | None = None,
) -> dict:
    filters = [Measurement.data_kind.in_(allowed_kinds(mode))]
    if basin_id:
        filters.append(Reservoir.basin_id == basin_id)
    if search:
        filters.append(Reservoir.name.icontains(search, autoescape=True))
    if start_date:
        filters.append(Measurement.observation_date >= start_date)
    if end_date:
        filters.append(Measurement.observation_date <= end_date)
    if data_kind:
        filters.append(Measurement.data_kind == data_kind)
    if source_id:
        filters.append(Measurement.source_id == source_id)
    latest_dates = (
        select(
            Measurement.reservoir_id.label("reservoir_id"),
            func.max(Measurement.observation_date).label("latest_date"),
        )
        .join(Reservoir, Measurement.reservoir_id == Reservoir.id)
        .where(*filters)
        .group_by(
            Measurement.reservoir_id,
        )
        .subquery()
    )
    rows = db.execute(
        select(Reservoir, Basin.name, Measurement)
        .join(
            Basin,
            Basin.id == Reservoir.basin_id,
        )
        .join(Measurement, Measurement.reservoir_id == Reservoir.id)
        .join(
            latest_dates,
            (latest_dates.c.reservoir_id == Reservoir.id)
            & (latest_dates.c.latest_date == Measurement.observation_date),
        )
        .where(*filters)
        .order_by(Reservoir.name, Reservoir.id)
    ).all()
    grouped = defaultdict(list)
    for reservoir, basin_name, measurement in rows:
        grouped[reservoir.id].append((reservoir, basin_name, measurement))
    snapshots = []
    for values in grouped.values():
        reservoir, basin_name, latest = values[0]
        snapshots.append(
            {
                "reservoir": reservoir,
                "basin_name": basin_name,
                "latest_date": latest.observation_date,
                "latest": latest if len(values) == 1 else None,
                "source_count": len(values),
            }
        )
    count = len(snapshots)
    dates = {item["latest_date"] for item in snapshots}
    kinds = {item["latest"].data_kind for item in snapshots if item["latest"] is not None}
    unambiguous = count > 0 and all(item["latest"] is not None for item in snapshots)
    comparable = unambiguous and len(dates) == 1 and len(kinds) == 1
    has_storage = comparable and all(item["latest"].storage_mm3 is not None for item in snapshots)
    storage = (
        sum((item["latest"].storage_mm3 for item in snapshots), Decimal(0)) if has_storage else None
    )
    capacities_verified = has_storage and all(
        item["reservoir"].capacity_mm3 is not None and item["reservoir"].capacity_source
        for item in snapshots
    )
    filling = None
    if capacities_verified:
        capacity = sum((item["reservoir"].capacity_mm3 for item in snapshots), Decimal(0))
        filling = (storage / capacity * 100).quantize(Decimal("0.01"))
    storage_status = (
        "available"
        if has_storage
        else (
            "no_data"
            if not count
            else "multiple_sources"
            if not unambiguous
            else "different_dates"
            if len(dates) != 1
            else "mixed_provenance"
            if len(kinds) != 1
            else "missing_storage"
        )
    )
    return {
        "mode": mode,
        "reservoirs": snapshots,
        "reservoir_count": count,
        "latest_observation_date": max(dates) if dates else None,
        "storage_mm3": storage,
        "weighted_filling_rate_pct": filling,
        "comparable_count": count if has_storage else 0,
        "storage_status": storage_status,
        "filling_status": "available"
        if filling is not None
        else ("unverified_capacities" if has_storage else storage_status),
    }


def quality(db: Session, mode: str) -> dict:
    kinds = allowed_kinds(mode)
    run_filter = IngestionRun.is_demo == (mode == "demo")
    imported, rejected, read = db.execute(
        select(
            func.count(IngestionRun.id),
            func.coalesce(func.sum(IngestionRun.rows_rejected), 0),
            func.coalesce(func.sum(IngestionRun.rows_read), 0),
        ).where(run_filter)
    ).one()

    def count_measurements(*conditions):
        return (
            db.scalar(
                select(func.count())
                .select_from(Measurement)
                .where(
                    Measurement.data_kind.in_(kinds),
                    *conditions,
                )
            )
            or 0
        )

    issues = (
        db.scalar(
            select(func.count())
            .select_from(QualityIssue)
            .join(
                IngestionRun,
                IngestionRun.id == QualityIssue.ingestion_run_id,
            )
            .where(run_filter, QualityIssue.resolved_at.is_(None))
        )
        or 0
    )
    return {
        "mode": mode,
        "files_ingested": imported,
        "rows_read": read,
        "rejected_rows": rejected,
        "observations": count_measurements(),
        "missing_storage": count_measurements(Measurement.storage_mm3.is_(None)),
        "missing_filling_rate": count_measurements(Measurement.filling_rate_pct.is_(None)),
        "unresolved_issues": issues,
    }
