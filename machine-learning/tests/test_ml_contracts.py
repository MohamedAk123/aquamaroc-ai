from datetime import date

import pytest
from aquamaroc_ml.baselines import moving_average, naive_last_value
from aquamaroc_ml.data_readiness import audit, write_report
from aquamaroc_ml.features import grouped_lags
from aquamaroc_ml.serving import unavailable_forecast
from aquamaroc_ml.splits import chronological_split
from aquamaroc_ml.train import main


def rows():
    return [
        {
            "reservoir_id": reservoir,
            "observation_date": f"2026-01-{day:02d}",
            "storage_mm3": day * factor,
            "data_kind": "DEMO",
        }
        for reservoir, factor in (("DEMO-A", 1), ("DEMO-B", 10))
        for day in (1, 2, 5, 8, 9)
    ]


def test_grouped_lags_do_not_leak_future_or_other_reservoir():
    original = rows()
    features = grouped_lags(original)
    assert features[1]["storage_lag_1"] == 1
    assert features[6]["storage_lag_1"] == 10
    assert features[2]["storage_lag_1"] is None  # 4 janvier absent.
    changed = [dict(r) for r in original]
    changed[4]["storage_mm3"] = 99999
    assert grouped_lags(changed)[:4] == features[:4]
    with pytest.raises(ValueError):
        grouped_lags(original, -1)


def test_temporal_split_purges_boundary_targets():
    split = chronological_split(rows(), date(2026, 1, 5), date(2026, 1, 9), 2)
    assert {r["observation_date"] for r in split["validation"]} == {"2026-01-05"}
    assert {r["observation_date"] for r in split["purged"]} == {"2026-01-08"}
    assert {r["observation_date"] for r in split["test"]} == {"2026-01-09"}


def test_baselines_on_explicit_demo_history():
    history = [1.0, 2.0, 3.0]
    assert naive_last_value(history) == 3
    assert moving_average(history, 2) == 2.5
    with pytest.raises(ValueError):
        naive_last_value([])


def test_audit_does_not_authorize_training(tmp_path, capsys):
    report = audit([], "OFFICIAL")
    assert report["decision"] == "insufficient_history"
    assert not report["ready_for_experiments"]
    write_report(report, tmp_path)
    assert (tmp_path / "data_readiness.json").exists()
    assert audit(rows(), "DEMO")["decision"] == "baseline_only"
    assert unavailable_forecast()["predicted_storage_mm3"] is None
    with pytest.raises(SystemExit) as error:
        main(["--audit", str(tmp_path / "data_readiness.json")])
    assert error.value.code == 1
    assert "J+7 (insufficient_history)" in capsys.readouterr().err
