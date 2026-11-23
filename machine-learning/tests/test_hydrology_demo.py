from datetime import date, timedelta

import pytest
from aquamaroc_ml.hydrology import (
    CAPACITY_MM3,
    DEMO_RESERVOIRS,
    FILLING_TARGET,
    HORIZON,
    TARGET,
    WeatherDay,
    horizon_features,
    simulate,
    simulate_filling,
    snow_balance,
    split_examples,
)
from aquamaroc_ml.weather import VARIABLE_UNITS, parse_forecast


def test_snow_accumulates_in_cold_weather_and_only_available_snow_melts():
    today = date(2026, 1, 1)
    pack, melt = snow_balance(4, WeatherDay(today, 2, 10, -2))
    assert (pack, melt) == (14, 0)
    assert snow_balance(pack, WeatherDay(today, 0, 0, 20)) == (0, 14)


def test_simulation_is_reproducible_bounded_and_chronological():
    states, examples = simulate(42, 5)
    assert (states, examples) == simulate(42, 5)
    assert all(row["data_kind"] == "DEMO" for row in states)
    assert all(0 <= row["storage_mm3"] <= CAPACITY_MM3 for row in states)
    assert any(row["snowfall_water_mm"] > 0 for row in states)
    assert any(row["melt_mm"] > 0 for row in states)
    assert any(row["rain_mm"] > 0 for row in states)
    train, val, test = split_examples(examples)
    assert train[-1]["target_date"] < val[0]["origin_date"]
    assert val[-1]["target_date"] < test[0]["origin_date"]
    first = train[0]
    assert date.fromisoformat(first["target_date"]) - date.fromisoformat(first["origin_date"]) == (
        timedelta(days=HORIZON)
    )
    actual = next(row for row in states if row["date"] == first["target_date"])
    assert first["storage_mm3"] + first[TARGET] == pytest.approx(actual["storage_mm3"])


def test_parse_open_meteo_checks_dates_units_and_missing_values():
    today = date(2026, 11, 23)
    daily = {
        "time": [(today + timedelta(days=i)).isoformat() for i in range(8)],
        "rain_sum": [999] + [2] * 7,
        "showers_sum": [1] * 8,
        "snowfall_sum": [4] * 8,
        "temperature_2m_mean": [-1] * 8,
    }
    payload = {"daily": daily, "daily_units": VARIABLE_UNITS.copy()}
    forecast = parse_forecast(payload, today)
    features = horizon_features(20, 0, forecast)
    assert forecast[0].day == today + timedelta(days=1)
    assert features["forecast_rain_mm"] == 21
    assert features["forecast_snow_water_mm"] == 28
    assert features["forecast_melt_mm"] == 0
    daily["rain_sum"][1] = None
    with pytest.raises(ValueError, match="invalide"):
        parse_forecast(payload, today)


def test_filling_targets_use_each_capacity_and_common_cutoffs():
    states, examples = simulate_filling(42, 5)
    measurements = {(row["reservoir"], row["date"]): row["storage_mm3"] for row in states}
    capacities = {reservoir.name: reservoir.capacity for reservoir in DEMO_RESERVOIRS}
    train, validation, test = split_examples(examples)
    assert train[-1]["target_date"] < validation[0]["origin_date"]
    assert validation[-1]["target_date"] < test[0]["origin_date"]
    for block in (train, validation, test):
        assert {row["reservoir"] for row in block} == set(capacities)
        assert all(0 <= row[FILLING_TARGET] <= 100 for row in block)
        for row in block[: len(capacities)]:
            name = row["reservoir"]
            assert row[FILLING_TARGET] == pytest.approx(
                100 * measurements[name, row["target_date"]] / capacities[name]
            )
