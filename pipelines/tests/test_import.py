from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from pipelines.ingestion.demo import DEMO_ROWS, RESERVOIR_IDS, SOURCE_ID, write_fixture
from pipelines.ingestion.import_xlsx import ImportFailure, import_file
from services.api.app.models import IngestionRun, Measurement, QualityIssue, Reservoir

MAPPING = Path("config/column_mapping.yaml")


def workbook(path, rows, sheet="Mesures_DEMO"):
    book = Workbook()
    page = book.active
    page.title = sheet
    page.append(["DEMO"])
    page.append(["Barrage", "Date du relevé", "Réserve (Mm3)", "Remplissage (%)"])
    for row in rows:
        page.append(row)
    book.save(path)
    book.close()
    return path


def run(engine, path, tmp_path, **kwargs):
    return import_file(engine, path, SOURCE_ID, MAPPING, "demo", tmp_path / "archive", **kwargs)


def test_valid_import_and_idempotency(seeded, tmp_path):
    path = tmp_path / "demo.xlsx"
    write_fixture(path)
    report = run(seeded, path, tmp_path)
    assert (report.status, report.rows_read, report.rows_valid, report.rows_rejected) == (
        "success",
        4,
        4,
        0,
    )
    second = run(seeded, path, tmp_path)
    assert second.reused and second.run_id == report.run_id
    with Session(seeded) as db:
        assert db.scalar(select(func.count()).select_from(Measurement)) == 4
        assert db.scalar(select(func.count()).select_from(IngestionRun)) == 1
        value = db.scalar(
            select(Measurement).where(
                Measurement.reservoir_id == RESERVOIR_IDS[0],
                Measurement.observation_date == date(2026, 1, 1),
            )
        )
        assert value.storage_mm3 == Decimal("12.7500")
        assert value.published_at is None and value.data_kind == "DEMO"
        reservoir = db.get(Reservoir, RESERVOIR_IDS[0])
        assert reservoir.latitude is reservoir.longitude is reservoir.geometry is None
        journal = db.scalar(select(IngestionRun))
        assert Path(journal.archive_path).read_bytes() == path.read_bytes()
        assert journal.provenance["dataset_url"] is None


@pytest.mark.parametrize(
    "bad",
    [
        ["Réservoir synthétique Alpha", "31/02/2026", "1", "20"],
        ["Réservoir synthétique Alpha", "2026-01-03", "1", "101"],
        ["Réservoir synthétique Alpha", "2026-01-03", "-1", "20"],
        ["Réservoir synthétique Alpha", "2026-01-03", None, None],
        ["Réservoir synthétique Alpha", "2026-01-03", "NaN", "20"],
        ["Réservoir synthétique Alpha", "2026-01-03", "=1+2", "20"],
        ["Nom inconnu", "2026-01-03", "1", "20"],
    ],
)
def test_rejections_are_logged(seeded, tmp_path, bad):
    path = workbook(tmp_path / "mixed.xlsx", [DEMO_ROWS[0], bad])
    report = run(seeded, path, tmp_path)
    assert (report.status, report.rows_valid, report.rows_rejected) == ("partial", 1, 1)
    assert report.rows_read == report.rows_valid + report.rows_rejected
    with Session(seeded) as db:
        issue = db.scalar(select(QualityIssue))
        assert issue.details["row"] == 4 and issue.details["reason"]
        assert "original" in issue.details


def test_duplicate_intra_file(seeded, tmp_path):
    report = run(seeded, workbook(tmp_path / "dupe.xlsx", [DEMO_ROWS[0]] * 2), tmp_path)
    assert report.rows_valid == report.rows_rejected == 1


@pytest.mark.parametrize("rows,sheet", [([], "Mesures_DEMO"), (DEMO_ROWS, "Inconnue")])
def test_empty_and_unknown_sheet(seeded, tmp_path, rows, sheet):
    report = run(seeded, workbook(tmp_path / "empty.xlsx", rows, sheet), tmp_path)
    assert report.status == "failed" and report.error
    with Session(seeded) as db:
        assert db.scalar(select(func.count()).select_from(Measurement)) == 0
        assert db.scalar(select(QualityIssue)).issue_type == "invalid_workbook"


def test_empty_file_and_invalid_extension(seeded, tmp_path):
    path = tmp_path / "empty.xlsx"
    path.touch()
    with pytest.raises(ValueError, match="vide"):
        run(seeded, path, tmp_path)
    path = tmp_path / "bad.csv"
    path.write_text("DEMO")
    with pytest.raises(ValueError, match="XLSX"):
        run(seeded, path, tmp_path)


def test_dry_run_has_no_side_effects(seeded, tmp_path):
    path = workbook(tmp_path / "demo.xlsx", DEMO_ROWS)
    report = run(seeded, path, tmp_path, dry_run=True)
    assert report.dry_run and report.rows_valid == 4 and report.run_id is None
    assert not (tmp_path / "archive").exists()
    with Session(seeded) as db:
        for model in (Measurement, IngestionRun, QualityIssue):
            assert db.scalar(select(func.count()).select_from(model)) == 0


def test_revision_conflict_preserves_original(seeded, tmp_path):
    run(seeded, workbook(tmp_path / "first.xlsx", [DEMO_ROWS[0]]), tmp_path)
    changed = list(DEMO_ROWS[0])
    changed[2] = "99"
    report = run(seeded, workbook(tmp_path / "changed.xlsx", [changed]), tmp_path)
    assert report.status == "failed" and report.rows_rejected == 1
    with Session(seeded) as db:
        assert db.scalar(select(Measurement)).storage_mm3 == Decimal("12.75")
        assert "Conflit" in db.scalar(select(QualityIssue)).details["reason"]


def test_rollback_on_database_error(seeded, tmp_path):
    path = workbook(tmp_path / "demo.xlsx", DEMO_ROWS)

    def fail(_mapper, _connection, _target):
        raise RuntimeError("Erreur simulée après création du journal")

    event.listen(Measurement, "before_insert", fail)
    try:
        with pytest.raises(ImportFailure, match="annulée"):
            run(seeded, path, tmp_path)
    finally:
        event.remove(Measurement, "before_insert", fail)
    with Session(seeded) as db:
        assert db.scalar(select(func.count()).select_from(Measurement)) == 0
        journal = db.scalar(select(IngestionRun))
        assert journal.status == "failed" and journal.rows_valid == 0
        assert journal.rows_read == journal.rows_rejected == 4


def test_mode_mismatch_rejected(seeded, tmp_path):
    path = workbook(tmp_path / "demo.xlsx", DEMO_ROWS)
    with pytest.raises(ValueError, match="incompatibles"):
        import_file(seeded, path, SOURCE_ID, MAPPING, "official", tmp_path / "archive")


def test_demo_setup_preserves_existing_fixture(seeded, tmp_path, monkeypatch):
    from pipelines.ingestion.demo import main

    monkeypatch.chdir(tmp_path)
    main()
    path = Path("data/demo/reservoirs_demo.xlsx")
    original = path.read_bytes()
    main()
    assert path.read_bytes() == original
