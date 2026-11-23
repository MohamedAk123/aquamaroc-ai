"""Import local XLSX avec provenance, archive et journal transactionnel."""

import argparse
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from pipelines.ingestion.mapping import load_mapping
from pipelines.ingestion.parser import parse_workbook
from pipelines.ingestion.tensift import TensiftMapping, parse_tensift
from services.api.app.core.config import get_settings
from services.api.app.core.logging import configure_logging
from services.api.app.db.base import utc_now
from services.api.app.db.session import get_engine
from services.api.app.models import DataSource, IngestionRun, Measurement, QualityIssue, Reservoir


@dataclass
class ImportReport:
    status: str
    rows_read: int
    rows_valid: int
    rows_rejected: int
    sha256: str
    run_id: str | None = None
    dry_run: bool = False
    reused: bool = False
    error: str | None = None


class ImportFailure(RuntimeError):
    pass


def archive_bytes(content: bytes, digest: str, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{digest}.xlsx"
    try:
        with path.open("xb") as stream:
            stream.write(content)
    except FileExistsError:
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ImportFailure("L'archive existante ne correspond pas à son empreinte") from None
    return path


def import_file(
    engine: Engine,
    file: Path,
    source_id: UUID,
    mapping_file: Path | TensiftMapping,
    mode: str,
    archive_dir: Path,
    dry_run: bool = False,
) -> ImportReport:
    if mode not in {"demo", "official"}:
        raise ValueError("Mode inconnu")
    mapping = load_mapping(mapping_file) if isinstance(mapping_file, Path) else mapping_file
    official_table = isinstance(mapping, TensiftMapping)
    if mode != "official" if official_table else mapping.mode != mode:
        raise ValueError("Le mapping et le mode sont incompatibles")
    if file.suffix.lower() != ".xlsx" or not file.is_file():
        raise ValueError("Fichier XLSX local requis")
    if not 0 < file.stat().st_size <= (10_000_000 if official_table else mapping.max_bytes):
        raise ValueError("Fichier vide ou trop volumineux")
    content = file.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    mapping_digest = hashlib.sha256(mapping.model_dump_json().encode()).hexdigest()
    if isinstance(mapping, TensiftMapping):
        if digest != mapping.sha256:
            raise ValueError("Empreinte différente du classeur audité")
        parsed = parse_tensift(content, mapping)
    else:
        parsed = parse_workbook(content, mapping)

    with Session(engine, expire_on_commit=False) as db:
        source = db.get(DataSource, source_id)
        if source is None:
            raise ValueError("Source inconnue : créer un référentiel vérifié avant l'import")
        if (source.verification_status == "DEMO") != (mode == "demo"):
            raise ValueError("La source et le mode sont incompatibles")
        kind = (
            "DEMO"
            if mode == "demo"
            else ("OFFICIAL" if source.verification_status == "VERIFIED" else "UNVERIFIED")
        )
        previous = db.scalar(
            select(IngestionRun).where(
                IngestionRun.source_id == source_id,
                IngestionRun.sha256 == digest,
                IngestionRun.is_demo == (mode == "demo"),
            )
        )
        if previous:
            if previous.mapping_sha256 != mapping_digest:
                raise ValueError("Mapping modifié : révision explicite de l'import nécessaire")
            return ImportReport(
                previous.status,
                previous.rows_read,
                previous.rows_valid,
                previous.rows_rejected,
                digest,
                str(previous.id),
                dry_run,
                reused=True,
                error=previous.error_summary,
            )

        accepted = []
        rejected = []
        for row in parsed.rows:
            if row.value is not None:
                if db.get(Reservoir, row.value.reservoir_id) is None:
                    row.error = "Identifiant de barrage absent de la base"
                else:
                    existing = db.scalar(
                        select(Measurement).where(
                            Measurement.reservoir_id == row.value.reservoir_id,
                            Measurement.observation_date == row.value.observation_date,
                            Measurement.source_id == source_id,
                            Measurement.data_kind == kind,
                        )
                    )
                    if existing:
                        same = (
                            existing.storage_mm3 == row.value.storage_mm3
                            and existing.filling_rate_pct == row.value.filling_rate_pct
                        )
                        row.error = "Doublon en base" if same else "Conflit de révision à vérifier"
            if row.error:
                rejected.append(row)
            else:
                accepted.append(row)

        count = len(parsed.rows)
        status = (
            "failed" if parsed.error or not accepted else ("partial" if rejected else "success")
        )
        summary = parsed.error or (f"{len(rejected)} ligne(s) rejetée(s)" if rejected else None)
        report = ImportReport(
            status, count, len(accepted), len(rejected), digest, dry_run=dry_run, error=summary
        )
        if dry_run:
            return report

        archive_path = archive_bytes(content, digest, archive_dir)
        run = IngestionRun(
            source_id=source_id,
            filename=file.name,
            sha256=digest,
            archive_path=str(archive_path),
            mapping_sha256=mapping_digest,
            provenance={
                "dataset_url": source.dataset_url,
                "license": source.license,
                "verification_status": source.verification_status,
                "source_title": source.title,
                "data_kind": kind,
                **(
                    {"resource_url": mapping.resource_url, "sheet": mapping.sheet}
                    if isinstance(mapping, TensiftMapping)
                    else {}
                ),
            },
            is_demo=mode == "demo",
            status="pending",
            rows_read=0,
            rows_valid=0,
            rows_rejected=0,
        )
        db.add(run)
        db.commit()  # Le journal survit à un rollback des mesures.
        report.run_id = str(run.id)
        try:
            for row in accepted:
                db.add(
                    Measurement(
                        **row.value.model_dump(),
                        source_id=source_id,
                        ingestion_run_id=run.id,
                        data_kind=kind,
                    )
                )
            for row in rejected:
                db.add(
                    QualityIssue(
                        ingestion_run_id=run.id,
                        issue_type="rejected_row",
                        severity="warning",
                        details={"row": row.number, "reason": row.error, "original": row.raw},
                    )
                )
            if parsed.error:
                db.add(
                    QualityIssue(
                        ingestion_run_id=run.id,
                        issue_type="invalid_workbook",
                        severity="error",
                        details={"reason": parsed.error},
                    )
                )
            run.status, run.completed_at = status, utc_now()
            run.rows_read, run.rows_valid, run.rows_rejected = count, len(accepted), len(rejected)
            run.error_summary = summary
            db.commit()
        except Exception as exc:
            db.rollback()
            run.status, run.completed_at = "failed", utc_now()
            run.rows_read, run.rows_valid, run.rows_rejected = count, 0, count
            run.error_summary = f"Transaction annulée ({type(exc).__name__})"
            db.commit()
            raise ImportFailure(run.error_summary) from exc
        logging.getLogger("aquamaroc.ingestion").info(json.dumps(asdict(report)))
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Import XLSX AquaMaroc AI")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--source-id", type=UUID, required=True)
    parser.add_argument("--mapping", type=Path, default=Path("config/column_mapping.yaml"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    configure_logging()
    settings = get_settings()
    try:
        report = import_file(
            get_engine(),
            args.file,
            args.source_id,
            args.mapping,
            settings.app_mode,
            settings.raw_archive_dir,
            args.dry_run,
        )
    except (ValueError, ImportFailure, OSError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(asdict(report), ensure_ascii=False))
    return 0 if report.status == "success" else 2 if report.status == "partial" else 1


if __name__ == "__main__":
    raise SystemExit(main())
