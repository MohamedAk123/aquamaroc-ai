from datetime import date
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from services.api.app.models import Basin, DataSource, IngestionRun, Measurement, Reservoir


def allowed_kinds(mode: str) -> tuple[str, ...]:
    return ("DEMO",) if mode == "demo" else ("OFFICIAL", "UNVERIFIED")


def visible_reservoirs(mode: str) -> Select:
    return select(Reservoir).where(
        select(Measurement.id)
        .where(
            Measurement.reservoir_id == Reservoir.id,
            Measurement.data_kind.in_(allowed_kinds(mode)),
        )
        .exists()
    )


def visible_basins(mode: str) -> Select:
    return select(Basin).where(
        Basin.id.in_(
            visible_reservoirs(mode).with_only_columns(Reservoir.basin_id),
        )
    )


def page(session: Session, statement: Select, limit: int, offset: int) -> dict:
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    return {
        "items": session.scalars(statement.limit(limit).offset(offset)).all(),
        "total": total or 0,
        "limit": limit,
        "offset": offset,
    }


def measurements(
    reservoir_id: UUID,
    mode: str,
    start: date | None,
    end: date | None,
    kind: str | None,
) -> Select:
    query = select(Measurement).where(
        Measurement.reservoir_id == reservoir_id,
        Measurement.data_kind.in_(allowed_kinds(mode)),
    )
    if start:
        query = query.where(Measurement.observation_date >= start)
    if end:
        query = query.where(Measurement.observation_date <= end)
    if kind:
        query = query.where(Measurement.data_kind == kind)
    return query.order_by(Measurement.observation_date, Measurement.id)


def freshness(session: Session, mode: str) -> list[dict]:
    sources = (
        select(DataSource)
        .where(
            DataSource.verification_status == "DEMO"
            if mode == "demo"
            else DataSource.verification_status != "DEMO",
        )
        .order_by(DataSource.title, DataSource.id)
    )
    items = []
    for source in session.scalars(sources):
        latest = session.execute(
            select(
                func.max(Measurement.observation_date),
                func.max(Measurement.published_at),
                func.max(Measurement.ingested_at),
            ).where(
                Measurement.source_id == source.id, Measurement.data_kind.in_(allowed_kinds(mode))
            )
        ).one()
        run = session.scalar(
            select(IngestionRun)
            .where(
                IngestionRun.source_id == source.id,
                IngestionRun.is_demo == (mode == "demo"),
            )
            .order_by(IngestionRun.started_at.desc())
            .limit(1)
        )
        items.append(
            {
                "source_id": source.id,
                "title": source.title,
                "producer": source.producer,
                "dataset_url": source.dataset_url,
                "license": source.license,
                "verification_status": source.verification_status,
                "checked_at": source.checked_at,
                "latest_observation_date": latest[0],
                "latest_published_at": latest[1],
                "latest_ingested_at": latest[2],
                "latest_run_status": run.status if run else None,
                "latest_run_completed_at": run.completed_at if run else None,
            }
        )
    return items
