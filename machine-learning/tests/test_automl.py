import sys
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from aquamaroc_ml.benchmarks import flaml_automl, h2o_automl, h2o_runtime
from aquamaroc_ml.benchmarks.dataset import FEATURES, TARGET, prepare_blocks
from aquamaroc_ml.data_readiness import audit
from aquamaroc_ml.train import ENGINES, benchmark, require_eligible

START = date(2025, 1, 1)
VALIDATION = START + timedelta(days=60)
TEST = START + timedelta(days=90)
CONFIG = {
    "advanced_training_enabled": True,
    "horizon_days": 7,
    "selection_metric": "mae",
    "split_strategy": "chronological_purged",
    "validation_start": VALIDATION.isoformat(),
    "test_start": TEST.isoformat(),
    "time_budget_seconds": 10,
    "seed": 42,
}


@pytest.fixture
def audited_sample():
    rows = []
    for i in range(110):
        day = START + timedelta(days=i)
        rows.append(
            {
                "reservoir_id": "fixture",
                "source_id": "test",
                "observation_date": day,
                "published_at": day.isoformat(),
                "storage_mm3": i,
                "data_kind": "OFFICIAL",
            }
        )
    # Exercise the reviewed-report branch using only in-memory test data.
    report = audit(rows, "OFFICIAL", split=(VALIDATION, TEST))
    report["ready_for_experiments"] = True
    report["windows"]["J+7"]["decision"] = "ready_for_experiments"
    return rows, report


def test_guard_disallows_other_horizon_demo_and_changed_snapshot(audited_sample):
    rows, report = audited_sample
    with pytest.raises(ValueError, match="désactivé"):
        require_eligible(report, CONFIG, 30)
    with pytest.raises(ValueError, match="désactivé"):
        require_eligible({**report, "data_kind": "DEMO"}, CONFIG, 7)
    with pytest.raises(ValueError, match="désactivée"):
        require_eligible(report, {**CONFIG, "advanced_training_enabled": False}, 7)
    with pytest.raises(ValueError, match="frontière"):
        require_eligible(report, {**CONFIG, "test_start": TEST.isoformat() + "x"}, 7)
    rows[-1]["storage_mm3"] = 123
    with pytest.raises(ValueError, match="empreinte"):
        benchmark(rows, report, CONFIG, 7, ["flaml"])


def test_preparation_checks_lag_publication_and_purges_boundary_targets(audited_sample):
    rows, _ = audited_sample
    rows[29]["published_at"] = (START + timedelta(days=31)).isoformat()
    train, validation = prepare_blocks(list(reversed(rows)), 7, VALIDATION, TEST)
    assert train[0]["storage_mm3"] == 31
    assert train[-1][TARGET] == 59
    assert validation[0]["storage_mm3"] == 60
    assert validation[-1][TARGET] == 89


class Frame:
    def __init__(self, rows, *, columns, dtype=None):
        self.cols = {name: [row[name] for row in rows] for name in columns}

    def __getitem__(self, key):
        if isinstance(key, list):
            return {name: self.cols[name] for name in key}
        return self.cols[key]


def test_runner_passes_same_rows_to_both_engines(audited_sample, monkeypatch):
    rows, report = audited_sample
    engines = {name: Mock(return_value={}) for name in ENGINES}
    for name, run in engines.items():
        monkeypatch.setitem(ENGINES, name, run)
    monkeypatch.setitem(sys.modules, "pandas", SimpleNamespace(DataFrame=Frame))
    result = benchmark(rows, report, CONFIG, 7, list(engines))
    train, validation = engines["flaml"].call_args.args
    assert engines["h2o"].call_args == engines["flaml"].call_args
    assert max(train[TARGET]) < min(validation["storage_mm3"])
    assert max(validation[TARGET]) == 89
    assert result["naive_last_value"]["mae_mm3"] == 7
    assert result["status"] == "validation_only"


def test_flaml_uses_explicit_holdout_and_retains_three_competitors(monkeypatch):
    row = dict.fromkeys(FEATURES, 1) | {TARGET: 4}
    frame = Frame([row], columns=[*FEATURES, TARGET])
    model = Mock(
        best_estimator="catboost",
        best_config={},
        best_loss_per_estimator={"catboost": 1, "lgbm": float("inf")},
    )
    model.predict.return_value = [3]
    monkeypatch.setitem(
        sys.modules, "flaml", SimpleNamespace(AutoML=lambda: model, __version__="test")
    )
    result = flaml_automl.run(frame, frame, budget_seconds=10, seed=42)
    settings = model.fit.call_args.kwargs
    assert settings["X_val"] == frame[list(FEATURES)]
    assert settings["y_val"] == [4]
    assert settings["estimator_list"] == ["catboost", "xgboost", "lgbm"]
    assert settings["eval_method"] == "holdout"
    assert settings["split_type"] == "time"
    assert settings["sample"] is settings["retrain_full"] is False
    assert settings["fit_kwargs_by_estimator"]["catboost"]["use_best_model"] is False
    assert settings["custom_hp"]["catboost"]["has_time"]["domain"] is True
    assert result["validation"]["mae_mm3"] == 1
    assert result["estimators_without_score"] == ["xgboost", "lgbm"]


def test_h2o_uses_only_explicit_frames_and_local_server(monkeypatch):
    monkeypatch.setattr(h2o_runtime, "system", lambda: "Linux")
    frame = Frame([dict.fromkeys(FEATURES, 1) | {TARGET: 4}], columns=[*FEATURES, TARGET])
    leader = Mock(model_id="test-model")
    leader.predict.return_value.as_data_frame.return_value = {"predict": [3]}
    model = Mock(leader=leader)
    model.leaderboard.as_data_frame.return_value = MagicMock()
    server = MagicMock()
    connection = MagicMock()
    create_automl = Mock(return_value=model)
    create_frame = Mock(side_effect=[object(), frame])
    monkeypatch.setitem(
        sys.modules,
        "h2o",
        SimpleNamespace(
            H2OFrame=create_frame, connect=Mock(return_value=connection), __version__="test"
        ),
    )
    monkeypatch.setitem(sys.modules, "h2o.automl", SimpleNamespace(H2OAutoML=create_automl))
    monkeypatch.setitem(
        sys.modules, "h2o.backend", SimpleNamespace(H2OLocalServer=SimpleNamespace(start=server))
    )
    monkeypatch.setitem(
        sys.modules,
        "h2o.estimators.xgboost",
        SimpleNamespace(H2OXGBoostEstimator=SimpleNamespace(available=lambda: True)),
    )
    result = h2o_automl.run(frame, frame, budget_seconds=10, seed=42)
    settings = create_automl.call_args.kwargs
    assert settings["nfolds"] == 0
    assert settings["exclude_algos"] == ["DRF", "StackedEnsemble"]
    args = model.train.call_args.kwargs
    assert args["training_frame"] is not frame
    assert args["leaderboard_frame"] is args["validation_frame"] is frame
    assert server.call_args.kwargs["bind_to_localhost"] is True
    connection.__exit__.assert_called_once()
    assert result["runtime"] == "native"
    assert result["validation"]["mae_mm3"] == 1


def test_h2o_container_uses_loopback_and_is_removed_after_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(h2o_runtime, "which", lambda _: "docker")
    command = Mock(side_effect=["container-id", "127.0.0.1:55001", "removed"])
    ready = Mock()
    monkeypatch.setattr(h2o_runtime, "docker_output", command)
    monkeypatch.setattr(h2o_runtime, "wait_for_server", ready)
    jar = tmp_path / "h2o.jar"

    with pytest.raises(ValueError, match="échec simulé"), h2o_runtime.docker_server(jar) as url:
        assert url == "http://127.0.0.1:55001"
        raise ValueError("échec simulé")

    launch, port, cleanup = (call.args for call in command.call_args_list)
    name = launch[launch.index("--name") + 1]
    assert launch[launch.index("--platform") + 1] == "linux/amd64"
    assert launch[launch.index("--publish") + 1] == "127.0.0.1::54321"
    assert (
        launch[launch.index("--mount") + 1]
        == f"type=bind,source={jar},target=/opt/h2o.jar,readonly"
    )
    assert port == ("docker", "port", name, "54321/tcp")
    assert cleanup == ("docker", "rm", "--force", name)
    ready.assert_called_once_with("http://127.0.0.1:55001")
