"""Métriques communes de régression en Mm³."""

from collections.abc import Iterable
from math import isfinite, sqrt
from statistics import mean


def regression_metrics(
    actual: Iterable[float], predicted: Iterable[float], *, unit: str = "mm3"
) -> dict[str, float]:
    errors = [
        float(estimate) - float(observed)
        for observed, estimate in zip(actual, predicted, strict=True)
    ]
    if not errors or not all(isfinite(error) for error in errors):
        raise ValueError("Les prédictions et cibles doivent être finies et non vides.")
    return {
        f"mae_{unit}": mean(abs(error) for error in errors),
        f"rmse_{unit}": sqrt(mean(error**2 for error in errors)),
        f"bias_{unit}": mean(errors),
    }
