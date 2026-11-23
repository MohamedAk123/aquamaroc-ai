import hashlib
from datetime import date
from decimal import Decimal

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from pipelines.ingestion.import_tensift import SOURCE_ID, seed_catalog
from pipelines.ingestion.import_xlsx import import_file
from pipelines.ingestion.tensift import CAPACITIES, TensiftMapping, parse_tensift
from services.api.app.models import IngestionRun, Measurement


def test_matrix_import_preserves_source_bytes_and_published_rate(seeded, tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Test"
    sheet.append(["Bassin", *(name for name in CAPACITIES for _ in range(2))])
    sheet.append(
        ["CAPACITÉ NORMALE\n(Mm³)", *(float(v) for v in CAPACITIES.values() for _ in range(2))]
    )
    sheet.append(["JOUR", *("RESERVE (Mm3)", "TAUX DE REMPLISSAGE\n ( % )") * 5])
    for day in range(1, 31):
        sheet.append([day, *(float(v) / 2 for v in CAPACITIES.values() for _ in (0,))])
        for i, capacity in enumerate(CAPACITIES.values()):
            sheet.cell(day + 3, 2 + 2 * i, float(capacity) / 2)
            sheet.cell(day + 3, 3 + 2 * i, 50.001)
    path = tmp_path / "synthetic-tensift.xlsx"
    workbook.save(path)
    payload = path.read_bytes()
    mapping = TensiftMapping(
        period=date(2026, 9, 1),
        sheet="Test",
        header_row=3,
        resource_url="https://example.test/synthetic.xlsx",
        sha256=hashlib.sha256(payload).hexdigest(),
    )
    parsed = parse_tensift(payload, mapping)
    assert parsed.error is None and len(parsed.rows) == 150
    assert parsed.rows[-1].value.observation_date == date(2026, 9, 30)
    seed_catalog(seeded)
    report = import_file(seeded, path, SOURCE_ID, mapping, "official", tmp_path / "archive")
    assert (report.rows_valid, report.rows_rejected) == (150, 0)
    assert import_file(seeded, path, SOURCE_ID, mapping, "official", tmp_path / "archive").reused
    with Session(seeded) as db:
        journal = db.scalar(select(IngestionRun).where(IngestionRun.source_id == SOURCE_ID))
        assert journal.provenance["resource_url"] == mapping.resource_url
        assert (tmp_path / "archive" / f"{report.sha256}.xlsx").read_bytes() == payload
        value = db.scalar(select(Measurement).where(Measurement.source_id == SOURCE_ID))
        assert value.data_kind == "OFFICIAL"
        assert value.filling_rate_pct == Decimal("50.0010")
        assert value.published_at is None
