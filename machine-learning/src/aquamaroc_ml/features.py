"""Décalages par dates exactes et par barrage, jamais par lignes inter-barrages."""

from datetime import date, timedelta


def grouped_lags(rows: list[dict], lag_days: int = 1) -> list[dict]:
    if lag_days < 1:
        raise ValueError("Décalage strictement passé requis")
    lookup = {}
    for row in rows:
        key = (row["reservoir_id"], date.fromisoformat(str(row["observation_date"])))
        if key in lookup:
            raise ValueError("Doublon barrage/date : audit nécessaire")
        lookup[key] = row["storage_mm3"]
    return [
        {
            **row,
            f"storage_lag_{lag_days}": lookup.get(
                (
                    row["reservoir_id"],
                    date.fromisoformat(str(row["observation_date"])) - timedelta(days=lag_days),
                )
            ),
        }
        for row in rows
    ]
