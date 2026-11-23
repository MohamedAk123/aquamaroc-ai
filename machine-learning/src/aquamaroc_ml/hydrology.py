"""Bilan hydrique synthétique d’un bassin montagneux et d’un barrage fictif."""

from dataclasses import dataclass
from datetime import date, timedelta
from math import cos, pi
from random import Random
from statistics import mean

HORIZON = 7
CAPACITY_MM3 = 120.0
TARGET = "delta_storage_mm3"
FEATURES = (
    "storage_mm3",
    "snow_water_mm",
    "forecast_rain_mm",
    "forecast_snow_water_mm",
    "forecast_melt_mm",
    "forecast_temperature_c",
)
FILLING_TARGET = "target_filling_pct"
FILLING_FEATURES = ("initial_filling_pct", "capacity_mm3", "catchment_km2", *FEATURES[1:])


@dataclass(frozen=True)
class DemoReservoir:
    name: str
    capacity: float
    catchment: float


DEMO_RESERVOIRS = (
    DemoReservoir("Barrage DEMO A", CAPACITY_MM3, 450.0),
    DemoReservoir("Barrage DEMO B", 75.0, 240.0),
    DemoReservoir("Barrage DEMO C", 190.0, 760.0),
)


@dataclass(frozen=True)
class WeatherDay:
    day: date
    rain_mm: float
    snow_water_mm: float
    temperature_c: float


def snow_balance(pack: float, weather: WeatherDay) -> tuple[float, float]:
    available = pack + weather.snow_water_mm
    melt = min(available, 2.5 * max(0.0, weather.temperature_c))
    return available - melt, melt


def horizon_features(storage: float, pack: float, forecast: list[WeatherDay]) -> dict:
    if len(forecast) != HORIZON:
        raise ValueError("Sept jours météo consécutifs sont requis.")
    if any(
        b.day - a.day != timedelta(days=1) for a, b in zip(forecast, forecast[1:], strict=False)
    ):
        raise ValueError("Les dates météo doivent être consécutives et ordonnées.")
    initial_pack = pack
    melts = []
    for weather in forecast:
        pack, melt = snow_balance(pack, weather)
        melts.append(melt)
    return {
        "storage_mm3": storage,
        "snow_water_mm": initial_pack,
        "forecast_rain_mm": sum(day.rain_mm for day in forecast),
        "forecast_snow_water_mm": sum(day.snow_water_mm for day in forecast),
        "forecast_melt_mm": sum(melts),
        "forecast_temperature_c": mean(day.temperature_c for day in forecast),
    }


def simulate(
    seed: int, years: int, reservoir: DemoReservoir = DEMO_RESERVOIRS[0]
) -> tuple[list[dict], list[dict]]:
    climate = Random(seed)
    forecast_noise = Random(seed + 1)
    days: list[WeatherDay] = []
    states: list[dict] = []
    storage, snow, flow = 70 * reservoir.capacity / CAPACITY_MM3, 0.0, 0.0
    start = date(2010, 1, 1)
    for index in range(years * 365):
        day = start + timedelta(days=index)
        winter = cos(2 * pi * (day.timetuple().tm_yday - 18) / 365.25)
        temperature = 9 - 10 * winter + climate.gauss(0, 2.8)
        wet = climate.random() < 0.22 + 0.14 * winter
        precipitation = min(100, climate.gammavariate(1.5, 7.5)) if wet else 0.0
        snow_fraction = min(1.0, max(0.0, (2 - temperature) / 4))
        snow_water = precipitation * snow_fraction
        rain = precipitation - snow_water
        weather = WeatherDay(day, rain, snow_water, temperature)
        days.append(weather)
        snow, melt = snow_balance(snow, weather)
        # 1 mm sur 1 km² = 0,001 Mm³. Aire et coefficients hypothétiques.
        flow = 0.45 * flow + 0.55 * reservoir.catchment * (0.32 * rain + 0.48 * melt) / 1000
        losses = (0.23 + 0.012 * max(0, temperature) + climate.uniform(0, 0.13)) * (
            reservoir.capacity / CAPACITY_MM3
        )
        storage = min(reservoir.capacity, max(0, storage + flow - losses))
        states.append(
            {
                "date": day.isoformat(),
                "data_kind": "DEMO",
                "reservoir": reservoir.name,
                "capacity_mm3": reservoir.capacity,
                "rain_mm": rain,
                "snowfall_water_mm": snow_water,
                "temperature_c": temperature,
                "snow_water_mm": snow,
                "melt_mm": melt,
                "inflow_mm3": flow,
                "losses_mm3": losses,
                "storage_mm3": storage,
            }
        )

    examples = []
    for origin in range(30, len(days) - HORIZON):
        forecast = []
        for lead, truth in enumerate(days[origin + 1 : origin + HORIZON + 1], start=1):
            scale = 0.18 + 0.06 * lead
            forecast.append(
                WeatherDay(
                    truth.day,
                    max(0.0, truth.rain_mm * (1 + forecast_noise.gauss(0, scale))),
                    max(0.0, truth.snow_water_mm * (1 + forecast_noise.gauss(0, scale))),
                    truth.temperature_c + forecast_noise.gauss(0, 0.7 + 0.18 * lead),
                )
            )
        state = states[origin]
        features = horizon_features(state["storage_mm3"], state["snow_water_mm"], forecast)
        target = states[origin + HORIZON]
        examples.append(
            {
                **features,
                "data_kind": "DEMO",
                "origin_date": state["date"],
                "target_date": target["date"],
                TARGET: target["storage_mm3"] - state["storage_mm3"],
            }
        )
    return states, examples


def filling_features(conditions: dict, reservoir: DemoReservoir) -> dict:
    return {
        **{name: conditions[name] for name in FEATURES[1:]},
        "initial_filling_pct": 100 * conditions["storage_mm3"] / reservoir.capacity,
        "capacity_mm3": reservoir.capacity,
        "catchment_km2": reservoir.catchment,
    }


def simulate_filling(seed: int, years: int) -> tuple[list[dict], list[dict]]:
    history, data = [], []
    for index, reservoir in enumerate(DEMO_RESERVOIRS):
        states, examples = simulate(seed + 100 * index, years, reservoir)
        history.extend(states)
        for example in examples:
            data.append(
                {
                    **filling_features(example, reservoir),
                    "reservoir": reservoir.name,
                    "data_kind": "DEMO",
                    "origin_date": example["origin_date"],
                    "target_date": example["target_date"],
                    FILLING_TARGET: 100
                    * (example["storage_mm3"] + example[TARGET])
                    / reservoir.capacity,
                }
            )
    data.sort(key=lambda row: (row["origin_date"], row["reservoir"]))
    return history, data


def split_examples(examples: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    validation = examples[len(examples) * 6 // 10]["origin_date"]
    test = examples[len(examples) * 8 // 10]["origin_date"]
    return (
        [row for row in examples if row["target_date"] < validation],
        [row for row in examples if validation <= row["origin_date"] and row["target_date"] < test],
        [row for row in examples if row["origin_date"] >= test],
    )
