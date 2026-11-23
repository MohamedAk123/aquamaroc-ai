"""Prévision quotidienne Open-Meteo pour le point de montagne d’Oukaïmeden."""

import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from math import isfinite
from urllib.parse import urlencode
from urllib.request import urlopen

from .hydrology import HORIZON, WeatherDay

LOCATION_SOURCE = "https://www.trappist.uliege.be/cms/c_5285930/en/site"
LATITUDE, LONGITUDE = 31.2061, -7.8664
VARIABLE_UNITS = {
    "rain_sum": "mm",
    "showers_sum": "mm",
    "snowfall_sum": "cm",
    "temperature_2m_mean": "°C",
}


def parse_forecast(payload: dict, issue_day: date) -> list[WeatherDay]:
    daily = payload["daily"]
    units = payload["daily_units"]
    if any(units.get(key) != unit for key, unit in VARIABLE_UNITS.items()):
        raise ValueError("Unités Open-Meteo inattendues.")
    dates = [date.fromisoformat(value) for value in daily["time"]]
    if len(set(dates)) != len(dates) or any(
        len(daily[key]) != len(dates) for key in VARIABLE_UNITS
    ):
        raise ValueError("Dimensions Open-Meteo incohérentes.")
    forecast = []
    for lead in range(1, HORIZON + 1):
        day = issue_day + timedelta(days=lead)
        if day not in dates:
            raise ValueError(f"Prévision Open-Meteo manquante pour le {day}.")
        index = dates.index(day)
        values = [daily[key][index] for key in VARIABLE_UNITS]
        if any(not isinstance(value, int | float) or not isfinite(value) for value in values):
            raise ValueError(f"Valeur météo manquante ou invalide pour le {day}.")
        rain, showers, snow_cm, temperature = values
        if min(rain, showers, snow_cm) < 0:
            raise ValueError(f"Précipitations négatives pour le {day}.")
        # Hypothèse DEMO : neige fraîche de 100 kg/m³, 1 cm ≈ 1 mm d’eau.
        forecast.append(WeatherDay(day, rain + showers, snow_cm, temperature))
    return forecast


def get_forecast() -> tuple[list[WeatherDay], dict, bytes]:
    from zoneinfo import ZoneInfo

    fetched = datetime.now(UTC)
    timezone = "Africa/Casablanca"
    issue_day = fetched.astimezone(ZoneInfo(timezone)).date()
    url = "https://api.open-meteo.com/v1/forecast?" + urlencode(
        {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "daily": ",".join(VARIABLE_UNITS),
            "timezone": timezone,
            "forecast_days": HORIZON + 1,
        }
    )
    with urlopen(url, timeout=25) as response:
        raw = response.read()
    payload = json.loads(raw)
    return (
        parse_forecast(payload, issue_day),
        {
            "provider": "Open-Meteo",
            "kind": "weather_model_forecast",
            "url": url,
            "retrieved_at_utc": fetched.isoformat(),
            "issue_date": issue_day.isoformat(),
            "payload_sha256": hashlib.sha256(raw).hexdigest(),
            "timezone": timezone,
            "mountain_point": "Observatoire d’Oukaïmeden",
            "coordinates_source": LOCATION_SOURCE,
            "grid_latitude": payload["latitude"],
            "grid_longitude": payload["longitude"],
            "grid_elevation_m": payload["elevation"],
        },
        raw,
    )
