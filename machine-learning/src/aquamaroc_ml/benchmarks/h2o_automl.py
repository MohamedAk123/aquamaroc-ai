"""Recherche H2O sur des frames chronologiques fournies par AquaMaroc."""

from time import perf_counter

from ..evaluate import regression_metrics
from .dataset import FEATURES, TARGET
from .h2o_runtime import h2o_connection


def require_xgboost() -> None:
    from h2o.estimators.xgboost import H2OXGBoostEstimator

    if not H2OXGBoostEstimator.available():
        raise RuntimeError("Le serveur H2O n’a pas chargé son moteur XGBoost natif.")


def check_runtime() -> dict:
    import h2o

    with h2o_connection() as runtime:
        require_xgboost()
        return {"version": h2o.__version__, "runtime": runtime, "xgboost_available": True}


def fit_automl(training_frame, validation_frame, features, target, *, budget_seconds, seed):
    from h2o.automl import H2OAutoML

    model = H2OAutoML(
        nfolds=0,
        exclude_algos=["DRF", "StackedEnsemble"],
        sort_metric="MAE",
        stopping_metric="MAE",
        max_runtime_secs=budget_seconds,
        seed=seed,
    )
    model.train(
        x=list(features),
        y=target,
        training_frame=training_frame,
        validation_frame=validation_frame,
        leaderboard_frame=validation_frame,
    )
    if model.leader is None:
        raise RuntimeError("H2O AutoML n’a terminé aucun modèle dans le budget fourni.")
    return model


def run(train, validation, *, budget_seconds: int, seed: int) -> dict:
    import h2o

    with h2o_connection() as runtime:
        require_xgboost()
        training_frame = h2o.H2OFrame(train)
        validation_frame = h2o.H2OFrame(validation)
        started = perf_counter()
        model = fit_automl(
            training_frame,
            validation_frame,
            FEATURES,
            TARGET,
            budget_seconds=budget_seconds,
            seed=seed,
        )
        search_seconds = perf_counter() - started
        leader = model.leader
        features = validation_frame[list(FEATURES)]
        started = perf_counter()
        predictions = leader.predict(features).as_data_frame()["predict"]
        prediction_seconds = perf_counter() - started
        leaderboard = model.leaderboard.as_data_frame()
        return {
            "version": h2o.__version__,
            "runtime": runtime,
            "candidate": leader.model_id,
            "leaderboard": leaderboard[["model_id", "mae", "rmse"]].to_dict("records"),
            "xgboost_available": True,
            "search_seconds": search_seconds,
            "prediction_seconds": prediction_seconds,
            "validation": regression_metrics(validation[TARGET], predictions),
        }
