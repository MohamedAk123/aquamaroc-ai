from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def parse_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value.strip(), pattern).date()
            except ValueError:
                pass
    raise ValueError("Date invalide (ISO 8601 ou JJ/MM/AAAA attendu)")


def parse_decimal(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("Nombre invalide")
    try:
        raw = str(value).strip().replace("\u202f", "").replace("\xa0", "").replace(" ", "")
        result = Decimal(raw.replace(",", "."))
        if not result.is_finite() or abs(result) >= Decimal("1000000000000"):
            raise ValueError("Nombre non fini ou trop grand")
        if result != result.quantize(Decimal("0.0001")):
            raise ValueError("Précision maximale : quatre décimales")
        return result
    except InvalidOperation as exc:
        raise ValueError("Nombre invalide") from exc
