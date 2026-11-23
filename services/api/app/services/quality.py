from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from services.api.app.models import DataSource, IngestionRun, Measurement, QualityIssue, Reservoir
from services.api.app.repositories.catalog import allowed_kinds, page
from services.api.app.schemas.dashboard import CoverageRead, ImportRead, IssueRead


def imports(db: Session, mode: str, limit: int, offset: int) -> dict:
    query = (
        select(IngestionRun)
        .where(IngestionRun.is_demo == (mode == "demo"))
        .order_by(IngestionRun.started_at.desc(), IngestionRun.id)
    )
    result = page(db, query, limit, offset)
    runs = result["items"]
    sources = {
        source.id: source
        for source in db.scalars(
            select(DataSource).where(DataSource.id.in_({run.source_id for run in runs}))
        )
    }
    result["items"] = [
        ImportRead(
            id=run.id,
            filename=run.filename,
            sha256=run.sha256,
            source_id=run.source_id,
            source_title=sources[run.source_id].title,
            source_checked_at=sources[run.source_id].checked_at,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            rows_read=run.rows_read,
            rows_valid=run.rows_valid,
            rows_rejected=run.rows_rejected,
        )
        for run in runs
    ]
    return {**result, "mode": mode}


def issues(
    db: Session, mode: str, limit: int, offset: int, run_id: UUID | None, open_only: bool
) -> dict:
    query = (
        select(QualityIssue)
        .join(IngestionRun, QualityIssue.ingestion_run_id == IngestionRun.id)
        .where(IngestionRun.is_demo == (mode == "demo"))
        .order_by(IngestionRun.started_at.desc(), QualityIssue.id)
    )
    if run_id:
        query = query.where(QualityIssue.ingestion_run_id == run_id)
    if open_only:
        query = query.where(QualityIssue.resolved_at.is_(None))
    result = page(db, query, limit, offset)
    rows = result["items"]
    filenames = dict(
        db.execute(
            select(IngestionRun.id, IngestionRun.filename).where(
                IngestionRun.id.in_({row.ingestion_run_id for row in rows})
            )
        ).all()
    )
    result["items"] = [
        IssueRead(
            id=row.id,
            ingestion_run_id=row.ingestion_run_id,
            filename=filenames[row.ingestion_run_id],
            issue_type=row.issue_type,
            severity=row.severity,
            resolved_at=row.resolved_at,
            row=row.details.get("row") if type(row.details.get("row")) is int else None,
            reason=row.details.get("reason")
            if isinstance(row.details.get("reason"), str)
            else None,
        )
        for row in rows
    ]
    return {**result, "mode": mode}


def coverage(db: Session, mode: str, limit: int, offset: int) -> dict:
    query = (
        select(
            Reservoir.id,
            Reservoir.name,
            DataSource.id,
            DataSource.title,
            Measurement.data_kind,
            func.min(Measurement.observation_date),
            func.max(Measurement.observation_date),
            func.count(distinct(Measurement.observation_date)),
        )
        .select_from(Measurement)
        .join(Reservoir, Measurement.reservoir_id == Reservoir.id)
        .join(DataSource, Measurement.source_id == DataSource.id)
        .where(Measurement.data_kind.in_(allowed_kinds(mode)))
        .group_by(
            Reservoir.id, Reservoir.name, DataSource.id, DataSource.title, Measurement.data_kind
        )
        .order_by(Reservoir.name, Reservoir.id, DataSource.id, Measurement.data_kind)
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = []
    for rid, name, sid, title, kind, first, last, count in db.execute(
        query.offset(offset).limit(limit)
    ):
        span = (last - first).days + 1
        items.append(
            CoverageRead(
                reservoir_id=rid,
                reservoir_name=name,
                source_id=sid,
                source_title=title,
                data_kind=kind,
                first_date=first,
                last_date=last,
                observed_days=count,
                span_days=span,
                gap_days=span - count,
            )
        )
    return {"items": items, "limit": limit, "offset": offset, "total": total, "mode": mode}
