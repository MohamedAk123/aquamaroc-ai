"""Préparer uniquement les blocs pré-test à partir de relevés horodatés."""

from collections import Counter
from datetime import date, timedelta

from ..forecast_readiness import as_date, publication_day

FEATURES = (
    "storage_mm3",
    "storage_lag_1",
    "storage_lag_7",
    "storage_lag_14",
    "storage_lag_30",
    "month",
)
TARGET = "target_storage_mm3"
LAGS = (1, 7, 14, 30)


def prepare_blocks(
    rows: list[dict], horizon: int, validation_start: date, test_start: date
) -> tuple[list[dict], list[dict]]:
    indexed = [(as_date(row["observation_date"]), str(row["reservoir_id"]), row) for row in rows]
    occurrences = Counter((day, reservoir) for day, reservoir, _ in indexed)
    indexed = sorted(
        (day, reservoir, row)
        for day, reservoir, row in indexed
        if occurrences[day, reservoir] == 1 and day < test_start
    )
    by_date = {(day, reservoir, row["source_id"]): row for day, reservoir, row in indexed}
    train, validation = [], []
    for day, reservoir, row in indexed:
        if publication_day(row) != day or row["storage_mm3"] is None:
            continue
        source = row["source_id"]
        boundary = validation_start if day < validation_start else test_start
        target_day = day + timedelta(days=horizon)
        target = by_date.get((target_day, reservoir, source))
        if not target or target["storage_mm3"] is None:
            continue
        target_publication = publication_day(target)
        if target_publication is None or not target_day <= target_publication < boundary:
            continue
        features = {"storage_mm3": float(row["storage_mm3"]), "month": day.month}
        for lag in LAGS:
            past = day - timedelta(days=lag)
            previous = by_date.get((past, reservoir, source))
            published = publication_day(previous) if previous else None
            if published is None or not past <= published <= day or previous["storage_mm3"] is None:
                break
            features[f"storage_lag_{lag}"] = float(previous["storage_mm3"])
        else:
            features[TARGET] = float(target["storage_mm3"])
            block = train if day < validation_start else validation
            block.append(features)
    if not train or not validation:
        raise ValueError("Aucun bloc train/validation exploitable avec les quatre lags vérifiés.")
    return train, validation
