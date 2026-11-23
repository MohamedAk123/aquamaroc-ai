"""Étude rétrospective Isolation Forest sur le lot officiel audité."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from services.api.app.db.session import get_engine
from services.api.app.services.variation_review import (
    REPORT,
    VariationReport,
    official_snapshot,
    snapshot_hash,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "machine-learning" / "src"))
from aquamaroc_ml.anomalies import study  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPORT)
    args = parser.parse_args()
    with Session(get_engine()) as db:
        rows = official_snapshot(db)
    audited = json.loads(
        (
            Path(__file__).resolve().parents[1] / "machine-learning/reports/data_readiness.json"
        ).read_text(encoding="utf-8")
    )
    if (
        audited["data_kind"] != "OFFICIAL"
        or len(rows) != audited["observation_count"]
        or {row["file_sha256"] for row in rows}
        != {entry["sha256"] for entry in audited["input_files"]}
    ):
        raise SystemExit("L’instantané officiel ne correspond plus au périmètre audité.")
    report = VariationReport(
        schema_version=1,
        study_sha256=snapshot_hash(rows),
        model="Isolation Forest",
        **study(rows, date(2026, 8, 1), date(2026, 10, 1), date(2026, 10, 31)),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(".tmp")
    temp.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    temp.replace(args.output)
    print(
        f"{report.reference_samples} exemples de référence, "
        f"{report.analysed_samples} analysés, {len(report.findings)} à examiner."
    )


if __name__ == "__main__":
    main()
