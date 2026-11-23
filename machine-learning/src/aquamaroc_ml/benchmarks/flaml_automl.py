"""Recherche FLAML sur un holdout fourni par AquaMaroc."""

from math import isfinite
from time import perf_counter

from ..evaluate import regression_metrics
from .dataset import FEATURES, TARGET

ESTIMATORS = ("catboost", "xgboost", "lgbm")


def run(train, validation, *, budget_seconds: int, seed: int) -> dict:
    from flaml import AutoML, __version__

    x_train = train[list(FEATURES)]
    x_validation = validation[list(FEATURES)]
    model = AutoML()
    started = perf_counter()
    model.fit(
        X_train=x_train,
        y_train=train[TARGET],
        X_val=x_validation,
        y_val=validation[TARGET],
        task="regression",
        estimator_list=list(ESTIMATORS),
        eval_method="holdout",
        split_type="time",
        metric="mae",
        time_budget=budget_seconds,
        seed=seed,
        n_jobs=1,
        sample=False,
        retrain_full=False,
        fit_kwargs_by_estimator={"catboost": {"use_best_model": False}},
        custom_hp={"catboost": {"has_time": {"domain": True}}},
    )
    search_seconds = perf_counter() - started
    if model.best_estimator is None:
        raise RuntimeError("FLAML n’a terminé aucun essai dans le budget fourni.")
    started = perf_counter()
    predictions = model.predict(x_validation)
    prediction_seconds = perf_counter() - started
    scores = {
        name: float(loss)
        for name, loss in model.best_loss_per_estimator.items()
        if loss is not None and isfinite(loss)
    }
    return {
        "version": __version__,
        "candidate": model.best_estimator,
        "candidate_config": model.best_config,
        "search_mae_by_estimator": scores,
        "estimators_without_score": [name for name in ESTIMATORS if name not in scores],
        "search_seconds": search_seconds,
        "prediction_seconds": prediction_seconds,
        "validation": regression_metrics(validation[TARGET], predictions),
    }
