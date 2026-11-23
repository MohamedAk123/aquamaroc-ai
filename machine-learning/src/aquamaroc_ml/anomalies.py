"""Classement rétrospectif des variations de réserve par barrage et source."""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal


def features(rows: list[dict]) -> list[dict]:
    series = defaultdict(dict)
    for row in rows:
        day = date.fromisoformat(row["observation_date"])
        key = (row["reservoir_id"], row["source_id"])
        if day in series[key]:
            raise ValueError("Doublon de barrage, source et jour")
        series[key][day] = row
    result = []
    for key in sorted(series):
        observations = series[key]
        for day, row in sorted(observations.items()):
            days = [day - timedelta(days=lag) for lag in range(8)]
            if any(d not in observations or observations[d]["storage_mm3"] is None for d in days):
                continue
            current, previous, week_ago = (
                Decimal(observations[days[lag]]["storage_mm3"]) for lag in (0, 1, 7)
            )
            result.append(
                {
                    **row,
                    "day": day,
                    "delta_1d_mm3": str(current - previous),
                    "delta_7d_mm3": str(current - week_ago),
                }
            )
    return result


def study(rows: list[dict], start: date, cutoff: date, end: date) -> dict:
    from sklearn import __version__
    from sklearn.ensemble import IsolationForest

    if not start < cutoff <= end:
        raise ValueError("Fenêtres chronologiques invalides")
    groups = defaultdict(list)
    scoped = [row for row in rows if start <= date.fromisoformat(row["observation_date"]) <= end]
    for sample in features(scoped):
        groups[sample["reservoir_id"], sample["source_id"]].append(sample)
    findings = []
    reference_count = analysed_count = 0
    for samples in groups.values():
        reference = [row for row in samples if row["day"] < cutoff]
        analysed = [row for row in samples if row["day"] >= cutoff]
        if len(reference) < 20 or not analysed:
            continue

        def matrix(block: list[dict]) -> list[list[float]]:
            return [[float(row["delta_1d_mm3"]), float(row["delta_7d_mm3"])] for row in block]

        raw_reference = matrix(reference)
        model = IsolationForest(n_estimators=128, n_jobs=1, random_state=42)
        model.fit(raw_reference)
        ranked = sorted(model.score_samples(raw_reference))
        # Seuil de tri défini uniquement sur la référence. Il ne mesure aucun risque.
        threshold = float(ranked[int(0.05 * (len(ranked) - 1))])
        scores = model.score_samples(matrix(analysed))
        reference_count += len(reference)
        analysed_count += len(analysed)
        for row, score in zip(analysed, scores, strict=True):
            if score < threshold:
                findings.append({**row, "score": float(score), "threshold": threshold})
    if not analysed_count:
        raise ValueError("Fenêtres de référence et d’analyse insuffisantes")
    return {
        "sklearn_version": __version__,
        "reference_start": start,
        "reference_end": cutoff - timedelta(days=1),
        "analysed_start": cutoff,
        "analysed_end": end,
        "input_observations": len(scoped),
        "reference_samples": reference_count,
        "analysed_samples": analysed_count,
        "findings": sorted(
            findings, key=lambda row: (row["score"], row["reservoir_name"], row["day"])
        ),
    }
