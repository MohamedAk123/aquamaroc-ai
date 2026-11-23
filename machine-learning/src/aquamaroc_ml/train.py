"""Exécuter les benchmarks AutoML locaux après revue des données officielles."""

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import yaml

from .benchmarks import flaml_automl, h2o_automl
from .benchmarks.dataset import FEATURES, TARGET, prepare_blocks
from .data_readiness import audit
from .evaluate import regression_metrics
from .forecast_readiness import as_date

ML_ROOT = Path("machine-learning")
ENGINES = {"flaml": flaml_automl.run, "h2o": h2o_automl.run}


def require_eligible(report: dict, config: dict, horizon: int) -> tuple[date, date]:
    window = report.get("windows", {}).get(f"J+{horizon}", {})
    decision = window.get("decision", report.get("decision", "indéterminé"))
    if (
        report.get("data_kind") != "OFFICIAL"
        or report.get("ready_for_experiments") is not True
        or decision != "ready_for_experiments"
        or window.get("has_three_verified_blocks") is not True
    ):
        raise ValueError(f"Entraînement avancé désactivé pour J+{horizon} ({decision}).")
    if (
        config.get("advanced_training_enabled") is not True
        or config.get("horizon_days") != horizon
        or config.get("selection_metric") != "mae"
        or config.get("split_strategy") != "chronological_purged"
    ):
        raise ValueError("Configuration de benchmark désactivée ou incompatible.")
    for boundary in ("validation_start", "test_start"):
        if config.get(boundary) != window.get(boundary):
            raise ValueError(f"La frontière {boundary} diffère de l’audit officiel.")
    return as_date(window["validation_start"]), as_date(window["test_start"])


def benchmark(
    rows: list[dict], report: dict, config: dict, horizon: int, engines: list[str]
) -> dict:
    bounds = require_eligible(report, config, horizon)
    budget = config.get("time_budget_seconds")
    seed = config.get("seed")
    if type(budget) is not int or budget <= 0 or type(seed) is not int or seed < 0:
        raise ValueError("Un budget entier positif et une graine entière sont requis.")
    if not rows or any(row.get("data_kind") != "OFFICIAL" for row in rows):
        raise ValueError("Le benchmark exige exclusivement des relevés officiels.")
    current = audit(rows, "OFFICIAL", split=bounds)
    if current["dataset_sha256"] != report.get("dataset_sha256"):
        raise ValueError("L’empreinte des relevés diffère de l’audit officiel.")
    window = current["windows"][f"J+{horizon}"]
    if not window["has_three_verified_blocks"]:
        raise ValueError("L’instantané actuel ne contient pas trois blocs vérifiés.")
    train, validation = prepare_blocks(rows, horizon, *bounds)

    import pandas as pd

    training_frame = pd.DataFrame(train, columns=[*FEATURES, TARGET], dtype=float)
    validation_frame = pd.DataFrame(validation, columns=[*FEATURES, TARGET], dtype=float)
    algorithms = {
        name: ENGINES[name](training_frame, validation_frame, budget_seconds=budget, seed=seed)
        for name in engines
    }
    return {
        "status": "validation_only",
        "data_kind": "OFFICIAL",
        "dataset_sha256": current["dataset_sha256"],
        "horizon_days": horizon,
        "validation_start": bounds[0].isoformat(),
        "test_start": bounds[1].isoformat(),
        "train_count": len(train),
        "validation_count": len(validation),
        "features": FEATURES,
        "time_budget_seconds_per_engine": budget,
        "seed": seed,
        "naive_last_value": regression_metrics(
            validation_frame[TARGET], validation_frame["storage_mm3"]
        ),
        "engines": algorithms,
    }


def main(argv: Sequence[str] = ()) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=(*ENGINES, "all"), default="all")
    parser.add_argument("--horizon", type=int, choices=(7, 30), default=7)
    parser.add_argument("--audit", type=Path, default=ML_ROOT / "reports/data_readiness.json")
    parser.add_argument("--output", type=Path, help="Écrire le bilan JSON de validation.")
    parser.add_argument(
        "--check-h2o", action="store_true", help="Vérifier H2O et XGBoost sans lire les relevés."
    )
    args = parser.parse_args(argv)
    config_path = ML_ROOT / f"configs/forecast_{args.horizon}d.yaml"
    try:
        if args.check_h2o:
            print(json.dumps(h2o_automl.check_runtime()))
            return
        report = json.loads(args.audit.read_text(encoding="utf-8"))
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        require_eligible(report, config, args.horizon)

        from scripts.audit_data import read_audit_inputs
        from services.api.app.core.config import get_settings

        if get_settings().app_mode != "official":
            raise ValueError("APP_MODE=official est requis.")
        rows, _ = read_audit_inputs("OFFICIAL")
        engines = list(ENGINES) if args.engine == "all" else [args.engine]
        results = benchmark(rows, report, config, args.horizon, engines)
        content = json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False, default=str)
        if args.output is None:
            print(content)
        else:
            args.output.write_text(content + "\n", encoding="utf-8")
    except ImportError as exc:
        parser.exit(1, f"Dépendance ML indisponible ({exc}). Voir machine-learning/README.md.\n")
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
