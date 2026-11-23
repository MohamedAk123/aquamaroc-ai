from datetime import date, timedelta

import pytest
from aquamaroc_ml.anomalies import features


def test_features_use_exact_past_days_and_keep_sources_separate():
    start = date(2026, 1, 1)
    rows = [
        {
            "reservoir_id": reservoir,
            "source_id": source,
            "observation_date": (start + timedelta(days=i)).isoformat(),
            "storage_mm3": str(i * scale),
        }
        for reservoir, source, scale in (("A", "source-a", 1), ("A", "source-b", 10))
        for i in range(9)
        if source != "source-b" or i != 2
    ]
    extracted = features(rows)
    assert [(row["source_id"], row["delta_1d_mm3"], row["delta_7d_mm3"]) for row in extracted] == [
        ("source-a", "1", "7"),
        ("source-a", "1", "7"),
    ]
    rows[8]["storage_mm3"] = "1000"
    assert features(rows)[0] == extracted[0]
    with pytest.raises(ValueError, match="Doublon"):
        features([*rows, rows[0]])
