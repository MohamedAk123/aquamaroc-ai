from collections.abc import Sequence


def naive_last_value(history: Sequence[float]) -> float:
    if not history:
        raise ValueError("Historique vide")
    return float(history[-1])


def moving_average(history: Sequence[float], window: int = 7) -> float:
    if not history or window < 1:
        raise ValueError("Historique non vide et fenêtre positive requis")
    values = history[-window:]
    return sum(values) / len(values)
