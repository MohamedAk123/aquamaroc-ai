import json
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from pipelines.ingestion.demo import RESERVOIR_IDS, SOURCE_ID
from pipelines.ingestion.import_xlsx import import_file
from services.api.app.core.config import Settings, get_settings
from services.api.app.db.session import get_session
from services.api.app.main import create_app
from services.api.app.models import IngestionRun, Measurement, QualityIssue


@pytest.fixture
def client(seeded, tmp_path):
    import_file(
        seeded,
        Path("data/demo/reservoirs_demo.xlsx"),
        SOURCE_ID,
        Path("config/column_mapping.yaml"),
        "demo",
        tmp_path / "archive",
    )
    app = create_app()

    def session():
        with Session(seeded) as db:
            yield db

    app.dependency_overrides[get_session] = session
    with TestClient(app) as client:
        yield client


def test_health_ready_and_openapi(client):
    assert client.get("/health").json() == {"status": "ok", "mode": "demo"}
    assert client.get("/ready").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/api/v1/reservoirs/{reservoir_id}/measurements" in schema["paths"]
    assert not any("prediction" in route for route in schema["paths"])


def test_default_mode_never_falls_back_to_demo(client, monkeypatch):
    monkeypatch.delenv("APP_MODE", raising=False)
    settings = Settings(_env_file=None)
    assert settings.app_mode == "official"
    client.app.dependency_overrides[get_settings] = lambda: settings
    response = client.get("/api/v1/overview").json()
    assert response["mode"] == "official"
    assert response["reservoirs"] == []
    assert response["storage_mm3"] is None


def test_variation_study_requires_matching_official_snapshot(client):
    url = "/api/v1/data/variation-review"
    assert client.get(url).json() == {"status": "unavailable", "mode": "demo", "report": None}
    client.app.dependency_overrides[get_settings] = lambda: Settings(app_mode="official")
    assert client.get(url).json() == {"status": "unavailable", "mode": "official", "report": None}


def test_demo_forecast_requires_separate_validated_artifact(client, tmp_path):
    path = tmp_path / "forecast.json"
    client.app.dependency_overrides[get_settings] = lambda: Settings(
        app_mode="official", demo_forecast_path=path
    )
    url = "/api/v1/demo/forecast"
    assert client.get(url).json() == {"status": "unavailable"}
    report = {
        "status": "experimental_synthetic_training",
        "data_kind": "DEMO",
        "target_kind": "filling_rate_pct",
        "horizon_days": 7,
        "target_date": "2026-01-08",
        "weather": {
            "provider": "Open-Meteo",
            "kind": "weather_model_forecast",
            "issue_date": "2026-01-01",
            "mountain_point": "Point de test",
        },
        "conditions": {
            "snow_water_mm": 12,
            "forecast_rain_mm": 2,
            "forecast_snow_water_mm": 2,
            "forecast_melt_mm": 6,
            "forecast_temperature_c": 3,
        },
        "reservoirs": [
            {
                "name": "Barrage DEMO Test",
                "capacity_mm3_demo": 100,
                "initial_filling_pct_demo": 50,
                "predicted_filling_pct_demo": 52.3,
                "predicted_storage_mm3_demo": 52.3,
                "h2o_filling_pct_demo": 52.3,
            }
        ],
        "selected_on_synthetic_validation": "h2o_automl",
        "h2o_candidate": "modele_test",
        "metrics_synthetic_only": {
            "test_selected": {"mae_pp": 0.7},
            "test_persistence": {"mae_pp": 1.2},
        },
        "mlflow_run_id": uuid4().hex,
    }
    path.write_text(json.dumps(report), encoding="utf-8")
    assert client.get(url).json()["reservoirs"][0]["predicted_filling_pct_demo"] == 52.3
    assert client.get("/api/v1/overview").json()["mode"] == "official"
    report["data_kind"] = "OFFICIAL"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert client.get(url).json() == {"status": "unavailable"}


def test_metrics_opt_in_and_no_identifier_label(monkeypatch):
    with monkeypatch.context() as env:
        env.setenv("METRICS_ENABLED", "true")
        get_settings.cache_clear()
        try:
            with TestClient(create_app()) as api:
                assert api.get("/health").status_code == 200
                assert api.get("/inconnu/identifiant-prive").status_code == 404
                text = api.get("/metrics").text
                assert 'route="/health",status="200"' in text
                assert 'route="unmatched",status="404"' in text
                assert "identifiant-prive" not in text
        finally:
            get_settings.cache_clear()


def test_quality_journal_modes_file_filter_and_coverage(client, seeded):
    with Session(seeded) as db:
        run = db.scalar(select(IngestionRun))
        db.add(
            QualityIssue(
                ingestion_run_id=run.id,
                issue_type="rejected_row",
                severity="warning",
                details={
                    "row": 7,
                    "reason": "Conflit de révision à vérifier",
                    "original": {"raw": "non publié"},
                },
            )
        )
        db.add(
            QualityIssue(
                ingestion_run_id=run.id,
                issue_type="rejected_row",
                severity="warning",
                details={"row": 8, "reason": "Doublon en base"},
                resolved_at=run.started_at,
            )
        )
        last = db.scalar(
            select(Measurement).where(
                Measurement.reservoir_id == RESERVOIR_IDS[0],
                Measurement.observation_date == date(2026, 1, 2),
            )
        )
        last.observation_date = date(2026, 1, 3)
        run_id = str(run.id)
        db.commit()
    base = "/api/v1/data/quality"
    entry = client.get(base + "/imports").json()["items"][0]
    assert entry["id"] == run_id and len(entry["sha256"]) == 64
    assert "archive_path" not in entry
    response = client.get(base + "/issues", params={"run_id": run_id, "open_only": True}).json()
    assert response["total"] == 1
    assert response["items"][0]["row"] == 7
    assert response["items"][0]["filename"] == entry["filename"]
    assert "original" not in response["items"][0]
    assert client.get(base + "/issues", params={"run_id": str(uuid4())}).json()["total"] == 0
    coverage = client.get(base + "/coverage").json()
    assert coverage["total"] == 2
    series = next(s for s in coverage["items"] if s["reservoir_id"] == str(RESERVOIR_IDS[0]))
    assert (series["observed_days"], series["span_days"], series["gap_days"]) == (2, 3, 1)
    client.app.dependency_overrides[get_settings] = lambda: Settings(app_mode="official")
    for resource in ("imports", "issues", "coverage"):
        payload = client.get(f"{base}/{resource}").json()
        assert payload["mode"] == "official" and payload["total"] == 0


def test_catalog_pagination_and_filters(client):
    basins = client.get("/api/v1/basins").json()
    assert basins["total"] == 1 and basins["mode"] == "demo"
    response = client.get("/api/v1/reservoirs", params={"limit": 1, "offset": 1})
    assert response.status_code == 200
    assert response.json()["total"] == 2 and len(response.json()["items"]) == 1
    filtered = client.get(
        "/api/v1/reservoirs",
        params={
            "basin_id": basins["items"][0]["id"],
            "search": "Alpha",
        },
    ).json()
    assert filtered["total"] == 1
    assert filtered["items"][0]["latitude"] is None
    assert client.get("/api/v1/reservoirs", params={"search": "%"}).json()["total"] == 0


def test_measurement_dates_decimals_and_provenance(client):
    data = client.get(
        f"/api/v1/reservoirs/{RESERVOIR_IDS[0]}/measurements",
        params={
            "start_date": "2026-01-02",
            "end_date": "2026-01-02",
        },
    ).json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["observation_date"] == "2026-01-02"
    assert item["storage_mm3"] == "13.1000"
    assert item["data_kind"] == "DEMO" and item["published_at"] is None
    assert item["ingested_at"].endswith("+00:00")


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/reservoirs?limit=0",
        "/api/v1/reservoirs?offset=-1",
        "/api/v1/reservoirs?basin_id=bad",
        f"/api/v1/reservoirs/{RESERVOIR_IDS[0]}/measurements?start_date=bad",
        f"/api/v1/reservoirs/{RESERVOIR_IDS[0]}/measurements?data_kind=OFFICIAL",
        f"/api/v1/reservoirs/{RESERVOIR_IDS[0]}/measurements?start_date=2026-02-01&end_date=2026-01-01",
    ],
)
def test_validation_errors(client, path):
    response = client.get(path)
    assert response.status_code == 422 and "error" in response.json()


def test_not_found_and_mode_isolation(client):
    assert client.get(f"/api/v1/reservoirs/{uuid4()}/measurements").status_code == 404
    client.app.dependency_overrides[get_settings] = lambda: Settings(app_mode="official")
    assert client.get("/api/v1/reservoirs").json()["items"] == []
    assert client.get("/api/v1/data/freshness").json()["items"] == []


def test_freshness(client):
    data = client.get("/api/v1/data/freshness").json()
    item = data["items"][0]
    assert item["latest_observation_date"] == "2026-01-02"
    assert item["latest_published_at"] is None
    assert item["latest_run_status"] == "success"
    assert item["verification_status"] == "DEMO"
    assert item["producer"] == "Générateur local"
    assert item["latest_ingested_at"].endswith("+00:00")


def test_unavailable_database_and_independent_liveness(client):
    from sqlalchemy.exc import OperationalError

    class Unavailable:
        def execute(self, *_args):
            raise OperationalError("SELECT", {}, Exception("offline"))

    client.app.dependency_overrides[get_session] = lambda: Unavailable()
    assert client.get("/ready").status_code == 503
    assert client.get("/health").status_code == 200


def test_cors_is_restricted(client):
    allowed = client.get("/health", headers={"Origin": "http://127.0.0.1:3000"})
    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
    response = client.options(
        "/api/v1/basins",
        headers={
            "Origin": "https://untrusted.invalid",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_overview_filters_and_safe_capacity(client):
    data = client.get("/api/v1/overview").json()
    assert data["reservoir_count"] == data["comparable_count"] == 2
    assert data["storage_mm3"] == "21.5000"
    assert data["weighted_filling_rate_pct"] is None
    assert data["filling_status"] == "unverified_capacities"
    assert data["latest_observation_date"] == "2026-01-02"
    assert data["reservoirs"][0]["latest"]["data_kind"] == "DEMO"
    filtered = client.get("/api/v1/overview?search=Alpha&end_date=2026-01-01").json()
    assert filtered["reservoir_count"] == 1 and filtered["storage_mm3"] == "12.7500"
    empty = client.get("/api/v1/overview?start_date=2027-01-01").json()
    assert empty["reservoir_count"] == 0 and empty["storage_mm3"] is None
    assert client.get("/api/v1/overview?data_kind=OFFICIAL").status_code == 422
    assert (
        client.get("/api/v1/overview?start_date=2026-02-01&end_date=2026-01-01").status_code == 422
    )


def test_weighted_filling_requires_sourced_capacities(client, seeded):
    from decimal import Decimal

    from services.api.app.models import Reservoir

    with Session(seeded) as db, db.begin():
        db.get(Reservoir, RESERVOIR_IDS[0]).capacity_mm3 = Decimal("100")
        db.get(Reservoir, RESERVOIR_IDS[1]).capacity_mm3 = Decimal("200")
    assert client.get("/api/v1/overview").json()["weighted_filling_rate_pct"] is None
    with Session(seeded) as db, db.begin():
        for reservoir_id in RESERVOIR_IDS:
            db.get(Reservoir, reservoir_id).capacity_source = "DEMO — référence synthétique de test"
    assert client.get("/api/v1/overview").json()["weighted_filling_rate_pct"] == "7.17"


def test_different_dates_are_not_summed(client, seeded):
    from datetime import date

    from sqlalchemy import delete

    from services.api.app.models import Measurement

    with Session(seeded) as db, db.begin():
        db.execute(
            delete(Measurement).where(
                Measurement.reservoir_id == RESERVOIR_IDS[1],
                Measurement.observation_date == date(2026, 1, 2),
            )
        )
    data = client.get("/api/v1/overview").json()
    assert data["storage_mm3"] is None and data["storage_status"] == "different_dates"


def test_multiple_sources_need_explicit_selection(client, seeded):
    from datetime import date

    from sqlalchemy import select

    from services.api.app.models import DataSource, IngestionRun, Measurement

    with Session(seeded) as db, db.begin():
        source = DataSource(
            title="DEMO autre source", source_type="synthetic", verification_status="DEMO"
        )
        db.add(source)
        db.flush()
        journal = db.scalar(select(IngestionRun))
        db.add(
            Measurement(
                reservoir_id=RESERVOIR_IDS[0],
                source_id=source.id,
                ingestion_run_id=journal.id,
                observation_date=date(2026, 1, 2),
                storage_mm3=99,
                data_kind="DEMO",
            )
        )
    data = client.get("/api/v1/overview").json()
    assert data["storage_mm3"] is None and data["storage_status"] == "multiple_sources"
    scoped = client.get(f"/api/v1/overview?source_id={SOURCE_ID}").json()
    assert scoped["storage_mm3"] == "21.5000"
    history = client.get(
        f"/api/v1/reservoirs/{RESERVOIR_IDS[0]}/measurements?source_id={SOURCE_ID}"
    )
    assert history.json()["total"] == 2


def test_detail_sources_quality_and_mode_boundaries(client):
    assert client.get(f"/api/v1/reservoirs/{RESERVOIR_IDS[0]}").json()["capacity_source"] is None
    assert client.get(f"/api/v1/reservoirs/{uuid4()}").status_code == 404
    assert client.get("/api/v1/sources").json()["items"][0]["verification_status"] == "DEMO"
    quality = client.get("/api/v1/data/quality").json()
    assert quality["observations"] == quality["rows_read"] == 4
    assert quality["files_ingested"] == 1 and quality["missing_storage"] == 0
    client.app.dependency_overrides[get_settings] = lambda: Settings(app_mode="official")
    assert client.get("/api/v1/overview").json()["reservoir_count"] == 0
    assert client.get("/api/v1/data/quality").json()["observations"] == 0
    assert client.get("/api/v1/sources").json()["items"] == []


def test_readiness_rejects_outdated_schema(client):
    from alembic import command
    from alembic.config import Config

    command.downgrade(Config("alembic.ini"), "0001_initial")
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "schema_outdated"
    assert client.get("/health").status_code == 200
