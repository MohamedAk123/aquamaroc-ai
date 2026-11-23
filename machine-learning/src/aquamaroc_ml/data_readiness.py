"""Audit descriptif sans entraînement ; aucune approbation automatique."""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, pstdev

from .forecast_readiness import audit_windows


def distribution(values: list[float]) -> dict | None:
    return (
        {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": mean(values),
            "std": pstdev(values),
        }
        if values
        else None
    )


def audit(
    rows: list[dict],
    data_kind: str,
    *,
    split: tuple[date, date] | None = None,
    input_files: list[dict] | None = None,
) -> dict:
    if any(row.get("data_kind", data_kind) != data_kind for row in rows):
        raise ValueError("Les catégories de provenance ne peuvent pas être mélangées")
    groups = defaultdict(list)
    for row in rows:
        groups[str(row["reservoir_id"])].append(row)
    summaries = {}
    for reservoir, observations in sorted(groups.items()):
        dates = sorted(date.fromisoformat(str(x["observation_date"])) for x in observations)
        unique = sorted(set(dates))
        gaps = [(b - a).days for a, b in zip(unique, unique[1:], strict=False)]
        values = [float(x["storage_mm3"]) for x in observations if x.get("storage_mm3") is not None]
        by_day = defaultdict(list)
        for row in observations:
            by_day[date.fromisoformat(str(row["observation_date"]))].append(row)
        deltas = []
        for first, last in zip(unique, unique[1:], strict=False):
            left, right = by_day[first], by_day[last]
            if (last - first).days == 1 and len(left) == len(right) == 1:
                current, following = left[0], right[0]
                if (
                    current.get("source_id") == following.get("source_id")
                    and current.get("storage_mm3") is not None
                    and following.get("storage_mm3") is not None
                ):
                    deltas.append(float(following["storage_mm3"] - current["storage_mm3"]))
        item = observations[0]
        summaries[reservoir] = {
            "name": item.get("reservoir_name", reservoir),
            "observations": len(observations),
            "first_date": dates[0].isoformat(),
            "last_date": dates[-1].isoformat(),
            "duplicates": len(dates) - len(unique),
            "interval_days": dict(Counter(gaps)),
            "missing_days_on_daily_grid": sum(max(0, gap - 1) for gap in gaps),
            "null_storage": sum(x.get("storage_mm3") is None for x in observations),
            "null_filling_rate": sum(x.get("filling_rate_pct") is None for x in observations),
            "missing_publication_dates": sum(not x.get("published_at") for x in observations),
            "storage_distribution": distribution(values),
            "daily_variation_mm3": distribution(deltas),
            "verified_capacity_mm3": (
                str(item["capacity_mm3"])
                if item.get("capacity_source") and item.get("capacity_mm3") is not None
                else None
            ),
            "capacity_source": item.get("capacity_source"),
        }
    timestamps = [date.fromisoformat(str(r["observation_date"])) for r in rows]
    fingerprint = sorted(
        json.dumps(r, default=str, sort_keys=True, ensure_ascii=False) for r in rows
    )
    windows = (
        {f"J+{horizon}": audit_windows(rows, horizon, *split) for horizon in (7, 30)}
        if split
        else {}
    )
    for window in windows.values():
        window["decision"] = (
            "baseline_only" if window["has_three_verified_blocks"] else "insufficient_history"
        )
    decision = (
        "baseline_only"
        if (data_kind == "DEMO" and rows)
        or (
            data_kind == "OFFICIAL"
            and any(w["has_three_verified_blocks"] for w in windows.values())
        )
        else "insufficient_history"
    )
    missing_publication = sum(not row.get("published_at") for row in rows)
    reason = (
        "Aucun relevé dans ce périmètre."
        if not rows
        else f"{missing_publication} dates de publication manquantes. "
        "Consulter les effectifs par horizon et par bloc avant toute comparaison. "
        "Aucune approbation d’entraînement avancé n’est émise par cet audit."
    )
    return {
        "data_kind": data_kind,
        "reservoir_count": len(groups),
        "observation_count": len(rows),
        "first_date": min(timestamps).isoformat() if timestamps else None,
        "last_date": max(timestamps).isoformat() if timestamps else None,
        "dataset_sha256": hashlib.sha256("\n".join(fingerprint).encode()).hexdigest(),
        "input_files": input_files or [],
        "reservoirs": summaries,
        "schema_note": (
            "Les éditions épinglées du Tensift comportent une ligne d’en-tête supplémentaire "
            "en octobre. L’import vérifié préserve les deux unités."
            if input_files
            and all(f.get("sheet") in {"Août_2026", "Sept_2026", "Oct_2026"} for f in input_files)
            else "Structure des fichiers non certifiée par cet audit."
        ),
        "weather_in_dataset": False,
        "missing_publication_dates": missing_publication,
        "windows": windows,
        "ready_for_experiments": False,
        "decision": decision,
        "reason": reason,
    }


def write_report(report: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "data_readiness.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        f"# Audit des données\n\nStatut : `{report['decision']}`.\n",
        f"{report['observation_count']} observations {report['data_kind']} · "
        f"{report['reservoir_count']} barrages.",
        f"Période : {report['first_date']} à {report['last_date']}.\n",
        report["reason"],
        "",
    ]
    for name, window in report["windows"].items():
        lines += [
            f"## {name}\n",
            f"- Décision : `{window['decision']}`.",
            f"- Frontières de validation et test : {window['validation_start']} "
            f"/ {window['test_start']}.",
            f"- Étendue : {window['calendar_span_days']} jours. "
            "Minimum calendaire pour trois blocs non vides : "
            f"{window['minimum_span_for_three_blocks']} jours, "
            "avant les lags et les retards de publication.",
            "",
            "| Bloc | Couples après purge | Avec les quatre lags | Publications vérifiées |",
            "|---|---:|---:|---:|",
        ]
        for block, label in (
            ("train", "Train"),
            ("validation", "Validation"),
            ("test", "Test final"),
        ):
            lines.append(
                f"| {label} | {window['calendar_pairs_after_purge'][block]} "
                f"| {window['calendar_pairs_with_all_lags'][block]} "
                f"| {window['pairs_with_verified_publication'][block]} |"
            )
        lines.append("")
    lines += [
        report["schema_note"],
        "",
        "Le JSON détaille les distributions, les variations quotidiennes, les capacités "
        "et les empreintes des fichiers. Aucune météo horodatée ne figure dans ce jeu.",
        "",
        "Aucun entraînement n'a été exécuté.",
    ]
    (directory / "data_readiness.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
