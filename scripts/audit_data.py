"""Rapport descriptif du contenu actuel de la base ; aucun entraînement."""

import argparse
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "machine-learning" / "src"))
from aquamaroc_ml.data_readiness import audit, write_report  # noqa: E402

from services.api.app.db.session import get_engine  # noqa: E402
from services.api.app.models import DataSource, IngestionRun, Measurement, Reservoir  # noqa: E402


def read_audit_inputs(kind: str) -> tuple[list[dict], list[dict]]:
    with Session(get_engine()) as db:
        query = (
            select(Measurement, Reservoir, IngestionRun)
            .join(Reservoir, Measurement.reservoir_id == Reservoir.id)
            .join(IngestionRun, Measurement.ingestion_run_id == IngestionRun.id)
            .join(DataSource, Measurement.source_id == DataSource.id)
            .where(Measurement.data_kind == kind, IngestionRun.is_demo == (kind == "DEMO"))
        )
        if kind == "OFFICIAL":
            query = query.where(DataSource.verification_status == "VERIFIED")
        values = list(db.execute(query))
        rows = [
            {
                "reservoir_id": str(x.reservoir_id),
                "reservoir_name": reservoir.name,
                "source_id": str(x.source_id),
                "data_kind": x.data_kind,
                "input_file_sha256": run.sha256,
                "observation_date": x.observation_date,
                "storage_mm3": x.storage_mm3,
                "filling_rate_pct": x.filling_rate_pct,
                "published_at": x.published_at,
                "capacity_mm3": reservoir.capacity_mm3,
                "capacity_source": reservoir.capacity_source,
            }
            for x, reservoir, run in values
        ]
        unique_runs = {run.id: run for _, _, run in values}
        files = [
            {
                "filename": run.filename,
                "sha256": run.sha256,
                "resource_url": run.provenance.get("resource_url"),
                "sheet": run.provenance.get("sheet"),
                "rejected_rows": run.rows_rejected,
            }
            for run in sorted(unique_runs.values(), key=lambda r: (r.filename, r.sha256))
        ]
    return rows, files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["OFFICIAL", "DEMO", "UNVERIFIED"], default="OFFICIAL")
    parser.add_argument("--output", type=Path, default=Path("machine-learning/reports/generated"))
    parser.add_argument("--validation-start", type=date.fromisoformat)
    parser.add_argument("--test-start", type=date.fromisoformat)
    args = parser.parse_args()
    if bool(args.validation_start) != bool(args.test_start):
        parser.error("Indiquer les deux frontières chronologiques")
    if args.validation_start and args.validation_start >= args.test_start:
        parser.error("La validation doit commencer avant le test")
    rows, files = read_audit_inputs(args.kind)
    split = (args.validation_start, args.test_start) if args.validation_start else None
    report = audit(rows, args.kind, split=split, input_files=files)
    write_report(report, args.output)
    print(f"{report['decision']} : {len(rows)} observation(s) {args.kind}. Aucun entraînement.")


if __name__ == "__main__":
    main()
