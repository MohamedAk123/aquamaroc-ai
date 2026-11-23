from datetime import date, timedelta


def chronological_split(
    rows: list[dict],
    validation_start: date,
    test_start: date,
    horizon_days: int,
) -> dict[str, list[dict]]:
    """Contrat préliminaire : disponibilité supposée à la date cible, sinon audit requis."""
    if validation_start >= test_start or horizon_days < 1:
        raise ValueError("Frontières chronologiques et horizon positif requis")
    result = {"train": [], "validation": [], "test": [], "purged": []}
    for row in rows:
        origin = date.fromisoformat(str(row["observation_date"]))
        target_date = origin + timedelta(days=horizon_days)
        if origin < validation_start:
            block = "train" if target_date < validation_start else "purged"
        elif origin < test_start:
            block = "validation" if target_date < test_start else "purged"
        else:
            block = "test"
        result[block].append(row)
    return result
