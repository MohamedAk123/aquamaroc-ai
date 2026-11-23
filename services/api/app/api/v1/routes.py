from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from services.api.app.core.config import Settings, get_settings
from services.api.app.db.session import get_session
from services.api.app.models import Basin, Reservoir
from services.api.app.repositories import catalog
from services.api.app.schemas.dashboard import (
    CoverageRead,
    ImportRead,
    IssueRead,
    OverviewRead,
    QualityRead,
)
from services.api.app.schemas.read import (
    BasinRead,
    DataKind,
    FreshnessRead,
    MeasurementRead,
    Page,
    ReservoirRead,
)
from services.api.app.services import dashboard, quality
from services.api.app.services.demo_forecast import DemoForecast, NoDemoForecast, read_demo_forecast
from services.api.app.services.variation_review import VariationReview, read_variation_review

router = APIRouter(prefix="/api/v1")


@router.get("/demo/forecast", response_model=DemoForecast | NoDemoForecast)
def demo_forecast(settings: Settings = Depends(get_settings)):
    return read_demo_forecast(settings.demo_forecast_path)


@router.get("/data/variation-review", response_model=VariationReview)
def variation_review(
    db: Session = Depends(get_session), settings: Settings = Depends(get_settings)
):
    return read_variation_review(db, settings.app_mode)


@router.get("/overview", response_model=OverviewRead)
def overview(
    basin_id: UUID | None = None,
    search: str | None = Query(None, max_length=200),
    start_date: date | None = None,
    end_date: date | None = None,
    data_kind: DataKind | None = None,
    source_id: UUID | None = None,
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, "start_date doit précéder end_date")
    if data_kind and data_kind not in catalog.allowed_kinds(settings.app_mode):
        raise HTTPException(422, "Provenance incompatible avec le mode actif")
    return dashboard.overview(
        db, settings.app_mode, basin_id, search, start_date, end_date, data_kind, source_id
    )


@router.get("/data/quality", response_model=QualityRead)
def data_quality(db: Session = Depends(get_session), settings: Settings = Depends(get_settings)):
    return dashboard.quality(db, settings.app_mode)


@router.get("/data/quality/imports", response_model=Page[ImportRead])
def quality_imports(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    return quality.imports(db, settings.app_mode, limit, offset)


@router.get("/data/quality/issues", response_model=Page[IssueRead])
def quality_issues(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    run_id: UUID | None = None,
    open_only: bool = False,
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    return quality.issues(db, settings.app_mode, limit, offset, run_id, open_only)


@router.get("/data/quality/coverage", response_model=Page[CoverageRead])
def quality_coverage(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    return quality.coverage(db, settings.app_mode, limit, offset)


@router.get("/sources", response_model=Page[FreshnessRead])
def sources(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    items = catalog.freshness(db, settings.app_mode)
    return {
        "items": items[offset : offset + limit],
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "mode": settings.app_mode,
    }


@router.get("/reservoirs/{reservoir_id}", response_model=ReservoirRead)
def reservoir_detail(
    reservoir_id: UUID,
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    item = db.scalar(
        catalog.visible_reservoirs(settings.app_mode).where(Reservoir.id == reservoir_id)
    )
    if item is None:
        raise HTTPException(404, "Barrage introuvable dans ce mode")
    return item


@router.get("/basins", response_model=Page[BasinRead])
def basins(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    return {
        **catalog.page(
            db, catalog.visible_basins(settings.app_mode).order_by(Basin.name), limit, offset
        ),
        "mode": settings.app_mode,
    }


@router.get("/reservoirs", response_model=Page[ReservoirRead])
def reservoirs(
    basin_id: UUID | None = None,
    search: str | None = Query(None, max_length=200),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    statement = catalog.visible_reservoirs(settings.app_mode)
    if basin_id:
        statement = statement.where(Reservoir.basin_id == basin_id)
    if search:
        statement = statement.where(Reservoir.name.icontains(search, autoescape=True))
    return {
        **catalog.page(db, statement.order_by(Reservoir.name, Reservoir.id), limit, offset),
        "mode": settings.app_mode,
    }


@router.get("/reservoirs/{reservoir_id}/measurements", response_model=Page[MeasurementRead])
def reservoir_measurements(
    reservoir_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    data_kind: DataKind | None = None,
    source_id: UUID | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, "start_date doit précéder end_date")
    if data_kind and data_kind not in catalog.allowed_kinds(settings.app_mode):
        raise HTTPException(422, "Provenance incompatible avec le mode actif")
    visible = catalog.visible_reservoirs(settings.app_mode).where(Reservoir.id == reservoir_id)
    if db.scalar(visible) is None:
        raise HTTPException(404, "Barrage introuvable dans ce mode")
    query = catalog.measurements(reservoir_id, settings.app_mode, start_date, end_date, data_kind)
    if source_id:
        from services.api.app.models import Measurement

        query = query.where(Measurement.source_id == source_id)
    return {**catalog.page(db, query, limit, offset), "mode": settings.app_mode}


@router.get("/data/freshness", response_model=Page[FreshnessRead])
def data_freshness(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    items = catalog.freshness(db, settings.app_mode)
    return {
        "items": items[offset : offset + limit],
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "mode": settings.app_mode,
    }
