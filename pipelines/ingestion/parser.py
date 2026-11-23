from dataclasses import dataclass, field
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from openpyxl import load_workbook

from pipelines.ingestion.mapping import ColumnMapping
from pipelines.normalization.values import parse_date, parse_decimal
from pipelines.validation.measurement import ValidatedMeasurement


@dataclass
class ParsedRow:
    number: int
    raw: dict[str, str | None]
    value: ValidatedMeasurement | None = None
    error: str | None = None


@dataclass
class ParseResult:
    rows: list[ParsedRow] = field(default_factory=list)
    error: str | None = None


def parse_workbook(content: bytes, mapping: ColumnMapping) -> ParseResult:
    try:
        with ZipFile(BytesIO(content)) as archive:
            if sum(x.file_size for x in archive.infolist()) > mapping.max_uncompressed_bytes:
                return ParseResult(error="Classeur décompressé trop volumineux")
        book = load_workbook(BytesIO(content), read_only=True, data_only=False)
    except (BadZipFile, OSError, ValueError, KeyError):
        return ParseResult(error="Classeur XLSX illisible")
    try:
        if mapping.sheet not in book.sheetnames:
            return ParseResult(error="Feuille inconnue")
        sheet = book[mapping.sheet]
        header = next(
            sheet.iter_rows(
                min_row=mapping.header_row, max_row=mapping.header_row, values_only=True
            ),
            (),
        )
        for name in mapping.columns.values():
            if header.count(name) != 1:
                return ParseResult(error=f"En-tête absent ou ambigu : {name}")
        indexes = {key: header.index(name) for key, name in mapping.columns.items()}
        result = ParseResult()
        seen = set()
        for number, values in enumerate(
            sheet.iter_rows(min_row=mapping.header_row + 1, values_only=True),
            mapping.header_row + 1,
        ):
            if not any(v is not None for v in values):
                continue
            raw = {
                key: values[index] if index < len(values) else None
                for key, index in indexes.items()
            }
            row = ParsedRow(number, {k: str(v) if v is not None else None for k, v in raw.items()})
            try:
                if any(isinstance(v, str) and v.startswith("=") for v in raw.values()):
                    raise ValueError("Formule non acceptée : fournir une valeur publiée")
                name = str(raw["reservoir_name"]).strip()
                if name not in mapping.reservoirs:
                    raise ValueError("Barrage absent du référentiel explicite")
                row.value = ValidatedMeasurement(
                    reservoir_id=mapping.reservoirs[name],
                    observation_date=parse_date(raw["observation_date"]),
                    storage_mm3=parse_decimal(raw["storage_mm3"]),
                    filling_rate_pct=parse_decimal(raw["filling_rate_pct"]),
                )
                key = (row.value.reservoir_id, row.value.observation_date)
                if key in seen:
                    raise ValueError("Doublon intra-fichier")
                seen.add(key)
            except ValueError as exc:
                row.value = None
                row.error = str(exc)
            result.rows.append(row)
        if not result.rows:
            result.error = "Aucune ligne de données"
        return result
    finally:
        book.close()
