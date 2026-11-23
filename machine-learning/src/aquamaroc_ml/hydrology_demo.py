"""Expérience DEMO J+7. Aucune lecture ni écriture dans la base officielle."""

import argparse
import hashlib
import json
from math import isfinite
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from .benchmarks.h2o_automl import fit_automl
from .benchmarks.h2o_runtime import h2o_connection
from .evaluate import regression_metrics
from .hydrology import (
    CAPACITY_MM3,
    DEMO_RESERVOIRS,
    FILLING_FEATURES,
    FILLING_TARGET,
    HORIZON,
    filling_features,
    horizon_features,
    simulate_filling,
    split_examples,
)
from .weather import get_forecast


def publish(output: Path, report: dict) -> None:
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=output, suffix=".tmp", delete=False
    ) as temporary:
        path = Path(temporary.name)
    try:
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        path.replace(output / "forecast_demo.json")
    finally:
        path.unlink(missing_ok=True)


def evaluate(frame, predictions) -> dict:
    return regression_metrics(frame[FILLING_TARGET], predictions.clip(0, 100), unit="pp")


def predict_reservoirs(leader, conditions: dict, filling: float, selected: str) -> list[dict]:
    import h2o
    import pandas as pd

    future = pd.DataFrame(
        [
            filling_features(
                {**conditions, "storage_mm3": reservoir.capacity * filling / 100}, reservoir
            )
            for reservoir in DEMO_RESERVOIRS
        ],
        columns=list(FILLING_FEATURES),
    )
    rates = leader.predict(h2o.H2OFrame(future)).as_data_frame()["predict"]
    results = []
    for reservoir, candidate in zip(DEMO_RESERVOIRS, rates, strict=True):
        if not isfinite(candidate):
            raise RuntimeError("Le modèle a renvoyé une prévision non finie.")
        candidate = min(100.0, max(0.0, float(candidate)))
        predicted = candidate if selected == "h2o_automl" else filling
        results.append(
            {
                "name": reservoir.name,
                "capacity_mm3_demo": reservoir.capacity,
                "initial_filling_pct_demo": filling,
                "h2o_filling_pct_demo": candidate,
                "predicted_filling_pct_demo": predicted,
                "predicted_storage_mm3_demo": reservoir.capacity * predicted / 100,
            }
        )
    return results


def refresh(output: Path, *, filling: float, snow_water: float) -> dict:
    """Recompute the published DEMO forecast with a saved H2O model."""
    import h2o
    import mlflow
    from mlflow import MlflowClient

    output = output.resolve()
    previous = json.loads((output / "forecast_demo.json").read_text(encoding="utf-8"))
    if (
        previous.get("data_kind") != "DEMO"
        or previous.get("target_kind") != "filling_rate_pct"
        or previous.get("status") != "experimental_synthetic_training"
        or previous.get("horizon_days") != HORIZON
    ):
        raise ValueError("Le dernier rapport ne contient pas de modèle de remplissage DEMO.")
    mlflow.set_tracking_uri(f"sqlite:///{(output / 'mlflow.db').as_posix()}")
    client = MlflowClient()
    training_id = previous.get("training_run_id", previous["mlflow_run_id"])
    training = client.get_run(training_id)
    tags = training.data.tags
    selected = tags.get("selected_model")
    if (
        training.info.status != "FINISHED"
        or tags.get("data_kind") != "DEMO"
        or tags.get("forecast_target") != "filling_rate_pct"
        or tags.get("dataset_sha256") != previous.get("dataset_sha256")
        or selected not in {"h2o_automl", "persistence"}
        or training.data.params.get("h2o_version") != h2o.__version__
    ):
        raise ValueError("Le run d’entraînement MLflow est incompatible.")
    model_name = previous["h2o_candidate"]
    if not any(
        item.path == model_name and not item.is_dir for item in client.list_artifacts(training_id)
    ):
        raise ValueError("Le modèle binaire H2O manque dans le run d’entraînement.")

    forecast, provenance, raw = get_forecast()
    conditions = horizon_features(0, snow_water, forecast)
    del conditions["storage_mm3"]
    with TemporaryDirectory() as directory:
        model_path = client.download_artifacts(training_id, model_name, directory)
        with h2o_connection() as runtime:
            h2o.no_progress()
            leader = h2o.upload_model(model_path)
            results = predict_reservoirs(leader, conditions, filling, selected)
        with mlflow.start_run(
            experiment_id=training.info.experiment_id,
            run_name="Prévision DEMO avec modèle sauvegardé",
            tags={
                "data_kind": "DEMO",
                "forecast_target": "filling_rate_pct",
                "training_run_id": training_id,
                "run_kind": "inference",
            },
        ) as tracked:
            report = {
                **previous,
                "weather": provenance,
                "target_date": forecast[-1].day.isoformat(),
                "conditions": conditions,
                "reservoirs": results,
                "h2o_runtime": runtime,
                "selected_on_synthetic_validation": selected,
                "training_run_id": training_id,
                "mlflow_run_id": tracked.info.run_id,
            }
            mlflow.log_params(
                {
                    "horizon_days": HORIZON,
                    "initial_filling_pct_demo": filling,
                    "initial_snow_water_mm_demo": snow_water,
                }
            )
            weather_file = Path(directory) / "open_meteo.json"
            weather_file.write_bytes(raw)
            mlflow.log_artifact(str(weather_file))
            mlflow.log_dict(report, "forecast_demo.json")
    publish(output, report)
    return report


def run(output: Path, *, seed: int, years: int, budget: int, filling: float, snow_water: float):
    import h2o
    import mlflow
    import pandas as pd
    from mlflow import MlflowClient

    forecast, provenance, raw = get_forecast()
    conditions = horizon_features(0, snow_water, forecast)
    del conditions["storage_mm3"]
    states, examples = simulate_filling(seed, years)
    train_rows, val_rows, test_rows = split_examples(examples)
    train, validation, test = (pd.DataFrame(rows) for rows in (train_rows, val_rows, test_rows))
    features = list(FILLING_FEATURES)
    cols = [*features, FILLING_TARGET]
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{(output / 'mlflow.db').as_posix()}")
    client = MlflowClient()
    experiment_name = "aquamaroc-remplissage-demo-j7"
    experiment = client.get_experiment_by_name(experiment_name)
    experiment_id = (
        experiment.experiment_id
        if experiment
        else client.create_experiment(
            experiment_name, artifact_location=(output / "artifacts").as_uri()
        )
    )
    snapshot = pd.DataFrame(states).to_csv(index=False, lineterminator="\n").encode()
    dataset_sha256 = hashlib.sha256(snapshot).hexdigest()
    with mlflow.start_run(experiment_id=experiment_id) as tracked:
        mlflow.set_tags(
            {
                "data_kind": "DEMO",
                "forecast_target": "filling_rate_pct",
                "weather_kind": provenance["kind"],
                "approved_for_display": "false",
                "dataset_sha256": dataset_sha256,
            }
        )
        mlflow.log_params(
            {
                "horizon_days": HORIZON,
                "seed": seed,
                "synthetic_years": years,
                "budget_seconds": budget,
                "reservoir_count_demo": len(DEMO_RESERVOIRS),
                "initial_filling_pct_demo": filling,
                "initial_snow_water_mm_demo": snow_water,
                "validation_start": val_rows[0]["origin_date"],
                "test_start": test_rows[0]["origin_date"],
                "n_train": len(train),
                "n_validation": len(validation),
                "n_test": len(test),
            }
        )
        with h2o_connection() as runtime, TemporaryDirectory() as directory:
            # L’AutoML reçoit exclusivement le train et la validation synthétiques.
            h2o.no_progress()
            model = fit_automl(
                h2o.H2OFrame(train[cols]),
                h2o.H2OFrame(validation[cols]),
                features,
                FILLING_TARGET,
                budget_seconds=budget,
                seed=seed,
            )
            leader = model.leader
            val_predictions = leader.predict(h2o.H2OFrame(validation[features]))
            val_h2o = evaluate(validation, val_predictions.as_data_frame()["predict"])
            val_persistence = evaluate(validation, validation["initial_filling_pct"])
            selected = (
                "h2o_automl" if val_h2o["mae_pp"] < val_persistence["mae_pp"] else "persistence"
            )
            test_baseline = evaluate(test, test["initial_filling_pct"])
            reservoirs = predict_reservoirs(leader, conditions, filling, selected)
            if selected == "h2o_automl":
                test_predictions = leader.predict(h2o.H2OFrame(test[features]))
                test_score = evaluate(test, test_predictions.as_data_frame()["predict"])
            else:
                test_score = test_baseline
            metrics = {
                "validation_h2o": val_h2o,
                "validation_persistence": val_persistence,
                "test_selected": test_score,
                "test_persistence": test_baseline,
            }
            report = {
                "data_kind": "DEMO",
                "status": "experimental_synthetic_training",
                "weather": provenance,
                "horizon_days": HORIZON,
                "target_kind": "filling_rate_pct",
                "target_date": forecast[-1].day.isoformat(),
                "conditions": conditions,
                "reservoirs": reservoirs,
                "selected_on_synthetic_validation": selected,
                "h2o_candidate": leader.model_id,
                "h2o_runtime": runtime,
                "dataset_sha256": dataset_sha256,
                "metrics_synthetic_only": metrics,
                "mlflow_run_id": tracked.info.run_id,
            }
            mlflow.log_params({"h2o_version": h2o.__version__, "h2o_runtime": runtime})
            mlflow.set_tag("selected_model", selected)
            mlflow.log_metrics(
                {
                    f"{stage}_{metric}": value
                    for stage, results in metrics.items()
                    for metric, value in results.items()
                }
            )
            temporary = Path(directory)
            (temporary / "synthetic_history.csv").write_bytes(snapshot)
            pd.DataFrame(examples).to_csv(
                temporary / "synthetic_supervised_examples.csv", index=False
            )
            (temporary / "open_meteo.json").write_bytes(raw)
            model.leaderboard.as_data_frame().to_csv(temporary / "h2o_leaderboard.csv", index=False)
            h2o.download_model(leader, path=directory)
            mlflow.log_artifacts(directory)
            mlflow.log_dict(report, "forecast_demo.json")
    publish(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".cache/hydrology-demo"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--years", type=int, default=10)
    parser.add_argument("--budget", type=int, default=25)
    parser.add_argument(
        "--predict-only", action="store_true", help="Recharger le modèle H2O suivi par MLflow."
    )
    initial = parser.add_mutually_exclusive_group()
    initial.add_argument(
        "--filling-pct", type=float, help="Taux initial fictif commun, 50 par défaut."
    )
    initial.add_argument(
        "--storage-mm3", type=float, help="Réserve initiale équivalente du barrage A."
    )
    parser.add_argument("--snow-water-mm", type=float, default=0.0)
    args = parser.parse_args()
    filling = args.filling_pct
    if filling is None:
        filling = 50.0 if args.storage_mm3 is None else 100 * args.storage_mm3 / CAPACITY_MM3
    if args.years < 5 or args.budget < 1 or not 0 <= filling <= 100:
        parser.error("Minimum cinq années, budget positif et taux initial dans [0, 100] %.")
    if not isfinite(args.snow_water_mm) or args.snow_water_mm < 0:
        parser.error("Le stock de neige initial doit être fini et positif ou nul.")
    try:
        if args.predict_only:
            report = refresh(args.output, filling=filling, snow_water=args.snow_water_mm)
        else:
            report = run(
                args.output,
                seed=args.seed,
                years=args.years,
                budget=args.budget,
                filling=filling,
                snow_water=args.snow_water_mm,
            )
    except (ImportError, OSError, KeyError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Expérience DEMO interrompue. {error}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
