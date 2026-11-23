"""Lecteur des classeurs mensuels publiés par l'agence du Tensift."""

from calendar import monthrange
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO
from uuid import UUID, uuid5
from zipfile import ZipFile

from openpyxl import load_workbook
from pydantic import BaseModel

from pipelines.ingestion.parser import ParsedRow, ParseResult
from pipelines.normalization.values import parse_decimal
from pipelines.validation.measurement import ValidatedMeasurement

BASIN_ID = UUID("ff676f36-f32a-44a7-891a-668ad7d58ea3")
CAPACITIES = {
    "Yacoub El Mansour": "57.45",
    "Lalla Takerkoust": "50.82",
    "Sd Mohamed Ben Slimane El Jazouli": "12.31",
    "Abou El Abess Sebti": "22.37",
    "Bge My abdrhmane": "58.99",
}


def reservoir_id(name: str) -> UUID:
    return uuid5(BASIN_ID, name)


class TensiftMapping(BaseModel):
    period: date
    sheet: str
    header_row: int
    resource_url: str
    sha256: str
    reader_version: int = 1


def parse_tensift(content: bytes, mapping: TensiftMapping) -> ParseResult:
    try:
        with ZipFile(BytesIO(content)) as archive:
            if sum(item.file_size for item in archive.infolist()) > 50_000_000:
                raise ValueError("Classeur décompressé trop volumineux")
        month = mapping.period
        days = monthrange(month.year, month.month)[1]
        book = load_workbook(BytesIO(content), read_only=True, data_only=True, keep_links=False)
        try:
            sheet = book[mapping.sheet]
            if sheet.max_row != mapping.header_row + days or sheet.max_column not in (11, 14):
                raise ValueError("Dimensions du tableau mensuel inattendues")
            rows = list(
                sheet.iter_rows(max_row=sheet.max_row, max_col=sheet.max_column, values_only=True)
            )
        finally:
            book.close()
        header = rows[mapping.header_row - 1]
        capacity = rows[mapping.header_row - 2]
        if isinstance(rows[0][0], datetime) and rows[0][0].date() != month:
            raise ValueError("Date du classeur incohérente")
        if header[0] != "JOUR" or capacity[0] != "CAPACITÉ NORMALE\n(Mm³)":
            raise ValueError("Colonne JOUR ou unité de capacité inattendue")
        if any(v is not None for row in rows for v in row[11:]):
            raise ValueError("Colonnes supplémentaires non vides")
        for i, (name, expected) in enumerate(CAPACITIES.items()):
            col = 1 + 2 * i
            paired_name = rows[0][col + 1]
            paired_capacity = capacity[col + 1]
            if (
                str(rows[0][col]).strip() != name
                or (paired_name is not None and str(paired_name).strip() != name)
                or parse_decimal(capacity[col]) != Decimal(expected)
                or (
                    paired_capacity is not None
                    and parse_decimal(paired_capacity) != Decimal(expected)
                )
                or header[col : col + 2] != ("RESERVE (Mm3)", "TAUX DE REMPLISSAGE\n ( % )")
            ):
                raise ValueError(f"Colonnes ou capacité inattendues pour {name}")
        result = ParseResult()
        for day, values in enumerate(rows[mapping.header_row :], 1):
            if type(values[0]) is not int or values[0] != day:
                raise ValueError(f"Jour absent, répété ou déplacé : {day}")
            for i, (name, maximum) in enumerate(CAPACITIES.items()):
                reserve, rate = values[1 + 2 * i : 3 + 2 * i]
                row = ParsedRow(
                    mapping.header_row + day,
                    {
                        "reservoir_name": name,
                        "day": str(day),
                        "storage_mm3": str(reserve),
                        "filling_rate_pct": str(rate),
                    },
                )
                try:
                    storage = parse_decimal(reserve)
                    published_rate = Decimal(str(rate)) if type(rate) in (int, float) else None
                    if storage is None or published_rate is None or not published_rate.is_finite():
                        raise ValueError("Réserve ou taux publié manquant")
                    if abs(published_rate - storage / Decimal(maximum) * 100) > Decimal("0.01"):
                        raise ValueError("Incohérence entre réserve, capacité et taux publié")
                    row.value = ValidatedMeasurement(
                        reservoir_id=reservoir_id(name),
                        observation_date=month.replace(day=day),
                        storage_mm3=storage,
                        filling_rate_pct=published_rate.quantize(
                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                        ),
                    )
                except ValueError as exc:
                    row.error = str(exc)
                result.rows.append(row)
        return result
    except (KeyError, OSError, ValueError) as exc:
        return ParseResult(error=str(exc))
