from datetime import date, timedelta

import pytest
from aquamaroc_ml.data_readiness import audit
from aquamaroc_ml.forecast_readiness import audit_windows

START = date(2026, 8, 1)
VALIDATION = date(2026, 9, 20)
TEST = date(2026, 10, 13)


def history(known_publication=False):
    result = []
    for i in range(92):
        day = START + timedelta(days=i)
        result.append(
            {
                "reservoir_id": "fixture",
                "source_id": "fixture",
                "data_kind": "OFFICIAL",  # Simulation du contrat, uniquement dans le test.
                "observation_date": day,
                "storage_mm3": i + 1,
                "filling_rate_pct": 50,
                "published_at": f"{day}T12:00:00+00:00" if known_publication else None,
            }
        )
    return result


def test_calendar_opportunity_does_not_imply_point_in_time_eligibility():
    result = audit(history(), "OFFICIAL", split=(VALIDATION, TEST))
    short = result["windows"]["J+7"]
    assert short["calendar_pairs_after_purge"] == {"train": 43, "validation": 16, "test": 12}
    assert short["calendar_pairs_with_all_lags"]["train"] == 13
    assert short["pairs_with_verified_publication"] == {"train": 0, "validation": 0, "test": 0}
    long = result["windows"]["J+30"]
    assert long["minimum_span_for_three_blocks"] == 93
    assert not long["has_three_calendar_blocks"]
    assert result["missing_publication_dates"] == 92
    assert result["decision"] == "insufficient_history"


def test_targets_use_exact_dates_and_delayed_labels_are_purged():
    rows = history(known_publication=True)
    before = audit_windows(rows, 7, VALIDATION, TEST)
    assert before["has_three_verified_blocks"]
    # 19 septembre : dernière cible de train avant le début de validation.
    target = next(r for r in rows if r["observation_date"] == VALIDATION - timedelta(days=1))
    target["published_at"] = f"{VALIDATION}T12:00:00+00:00"
    after = audit_windows(rows, 7, VALIDATION, TEST)
    assert after["calendar_pairs_after_purge"] == before["calendar_pairs_after_purge"]
    assert after["pairs_with_verified_publication"]["train"] == 42
    rows.remove(target)
    without_target = audit_windows(rows, 7, VALIDATION, TEST)
    assert without_target["calendar_pairs_after_purge"]["train"] == 42
    target["data_kind"] = "DEMO"
    with pytest.raises(ValueError, match="provenance"):
        audit([*rows, target], "OFFICIAL", split=(VALIDATION, TEST))
