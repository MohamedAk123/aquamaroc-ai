"""Faisabilité chronologique des cibles, sans ajustement de modèle."""

from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta


def as_date(value: object) -> date:
    return date.fromisoformat(str(value))


def publication_day(row: dict) -> date | None:
    value = row.get("published_at")
    if not value:
        return None
    timestamp = datetime.fromisoformat(str(value))
    return timestamp.astimezone(UTC).date() if timestamp.tzinfo else timestamp.date()


def audit_windows(rows: list[dict], horizon: int, validation_start: date, test_start: date) -> dict:
    """Dates communes, cibles exactes, purge stricte aux frontières.

    La couverture « vérifiée » compte seulement les couples dont l'information
    à l'origine et la disponibilité des cibles pré-test sont démontrées.
    Une publication manquante n'est jamais remplacée par une date de mesure.
    """
    if horizon < 1 or validation_start >= test_start:
        raise ValueError("Horizon positif et frontières ordonnées requis")
    grouped = defaultdict(list)
    for row in rows:
        key = (row["reservoir_id"], row.get("source_id"), as_date(row["observation_date"]))
        grouped[key].append(row)
    blocks = ("train", "validation", "test")
    calendar = Counter(dict.fromkeys(blocks, 0))
    full_lags = calendar.copy()
    verified = calendar.copy()
    origins = defaultdict(set)
    purged = 0
    ambiguous = 0
    names_at_date = Counter((reservoir, origin) for reservoir, _, origin in grouped)
    for (reservoir, source, origin), matches in grouped.items():
        if len(matches) != 1 or names_at_date[(reservoir, origin)] != 1:
            ambiguous += len(matches)
            continue
        row = matches[0]
        target_date = origin + timedelta(days=horizon)
        targets = grouped.get((reservoir, source, target_date), [])
        if (
            len(targets) != 1
            or names_at_date[(reservoir, target_date)] != 1
            or row.get("storage_mm3") is None
            or targets[0].get("storage_mm3") is None
        ):
            continue
        if origin < validation_start:
            block, boundary = "train", validation_start
        elif origin < test_start:
            block, boundary = "validation", test_start
        else:
            block, boundary = "test", None
        if boundary and target_date >= boundary:
            purged += 1
            continue
        calendar[block] += 1
        origins[block].add(origin)
        lags = [
            grouped.get((reservoir, source, origin - timedelta(days=lag)), [])
            for lag in (1, 7, 14, 30)
        ]
        if all(len(items) == 1 and items[0].get("storage_mm3") is not None for items in lags):
            full_lags[block] += 1
        origin_publication = publication_day(row)
        target_publication = publication_day(targets[0])
        if (
            origin_publication == origin
            and target_publication is not None
            and target_publication >= target_date
            and (boundary is None or target_publication < boundary)
        ):
            verified[block] += 1
    dates = [day for _, _, day in grouped]
    span = (max(dates) - min(dates)).days + 1 if dates else 0
    return {
        "horizon_days": horizon,
        "validation_start": validation_start.isoformat(),
        "test_start": test_start.isoformat(),
        "calendar_span_days": span,
        "minimum_span_for_three_blocks": 3 * (horizon + 1),
        "calendar_pairs_after_purge": dict(calendar),
        "distinct_origin_days": {block: len(origins[block]) for block in blocks},
        "calendar_pairs_with_all_lags": dict(full_lags),
        "pairs_with_verified_publication": dict(verified),
        "purged_pairs": purged,
        "ambiguous_origins": ambiguous,
        "has_three_calendar_blocks": all(calendar[block] for block in blocks),
        "has_three_verified_blocks": all(verified[block] for block in blocks),
    }
