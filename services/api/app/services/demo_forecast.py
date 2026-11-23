"""Read the published synthetic study without accessing the official catalog."""

import logging
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, FiniteFloat, ValidationError

logger = logging.getLogger(__name__)
Rate = Annotated[FiniteFloat, Field(ge=0, le=100)]
NonNegative = Annotated[FiniteFloat, Field(ge=0)]


class DemoReservoir(BaseModel):
    name: str = Field(pattern=r"^Barrage DEMO( .+)?$")
    capacity_mm3_demo: FiniteFloat = Field(gt=0)
    initial_filling_pct_demo: Rate
    h2o_filling_pct_demo: Rate
    predicted_filling_pct_demo: Rate
    predicted_storage_mm3_demo: NonNegative


class Weather(BaseModel):
    provider: Literal["Open-Meteo"]
    kind: Literal["weather_model_forecast"]
    issue_date: date
    mountain_point: str


class Scenario(BaseModel):
    snow_water_mm: NonNegative
    forecast_rain_mm: NonNegative
    forecast_snow_water_mm: NonNegative
    forecast_melt_mm: NonNegative
    forecast_temperature_c: FiniteFloat


class Score(BaseModel):
    mae_pp: NonNegative


class SyntheticMetrics(BaseModel):
    test_selected: Score
    test_persistence: Score


class DemoForecast(BaseModel):
    data_kind: Literal["DEMO"]
    status: Literal["experimental_synthetic_training"]
    horizon_days: Literal[7]
    target_kind: Literal["filling_rate_pct"]
    target_date: date
    weather: Weather
    conditions: Scenario
    reservoirs: list[DemoReservoir] = Field(min_length=1)
    selected_on_synthetic_validation: Literal["h2o_automl", "persistence"]
    h2o_candidate: str
    metrics_synthetic_only: SyntheticMetrics
    mlflow_run_id: str = Field(pattern=r"^[0-9a-f]{32}$")


class NoDemoForecast(BaseModel):
    status: Literal["unavailable"] = "unavailable"


def read_demo_forecast(path: Path | None) -> DemoForecast | NoDemoForecast:
    if path is None:
        return NoDemoForecast()
    try:
        return DemoForecast.model_validate_json(path.read_bytes())
    except FileNotFoundError:
        return NoDemoForecast()
    except (OSError, ValidationError):
        logger.warning("Le rapport local de la prévision DEMO est illisible ou incompatible.")
        return NoDemoForecast()
