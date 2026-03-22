"""Weather tools using the Open-Meteo API (no API key required)."""

from __future__ import annotations

import contextvars
import datetime
from typing import Any

import httpx

from config.settings import OPEN_METEO_FORECAST_URL, WMO_CODE_MAP
from utils.geocoding import geocode_location

# ---------------------------------------------------------------------------
# Temperature unit context variable — set this before running the agent so
# all weather tool calls in the same thread respect the user's preference.
# ---------------------------------------------------------------------------
_temperature_unit_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "temperature_unit", default="fahrenheit"
)


def set_temperature_unit(unit: str) -> None:
    """Set the temperature unit for the current context ('fahrenheit' or 'celsius')."""
    _temperature_unit_var.set(unit.lower())


def get_temperature_unit() -> str:
    """Return the temperature unit for the current context."""
    return _temperature_unit_var.get()


def _wmo_desc(code: int) -> str:
    return WMO_CODE_MAP.get(code, f"Weather code {code}")


def get_current_weather(location: str) -> dict[str, Any]:
    """Return current weather conditions for a location.

    Args:
        location: Human-readable location string (e.g. "Austin, TX").

    Returns:
        Dictionary with temperature, humidity, wind, precipitation, UV index,
        feels-like temperature, and a human-readable weather description.
    """
    lat, lon = geocode_location(location)
    temperature_unit = get_temperature_unit()
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "uv_index",
        ],
        "wind_speed_unit": "kmh",
        "temperature_unit": temperature_unit,
        "timezone": "auto",
    }
    with httpx.Client(timeout=15) as client:
        resp = client.get(OPEN_METEO_FORECAST_URL, params=params)
        resp.raise_for_status()
    data = resp.json()
    current = data.get("current", {})
    return {
        "location": location,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": current.get("temperature_2m"),
        "feels_like_c": current.get("apparent_temperature"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_direction_deg": current.get("wind_direction_10m"),
        "precipitation_mm": current.get("precipitation"),
        "weather_code": current.get("weather_code"),
        "weather_description": _wmo_desc(current.get("weather_code", 0)),
        "uv_index": current.get("uv_index"),
        "timestamp": current.get("time", datetime.datetime.now(datetime.UTC).isoformat()),
        "temperature_unit": temperature_unit,
    }


def get_15min_nowcast(location: str) -> dict[str, Any]:
    """Return minute-by-minute precipitation nowcast for the next 15 minutes.

    Args:
        location: Human-readable location string.

    Returns:
        Dictionary with per-minute precipitation values and a natural-language
        summary like "Rain starts in 8 minutes".
    """
    lat, lon = geocode_location(location)
    params = {
        "latitude": lat,
        "longitude": lon,
        "minutely_15": ["precipitation", "weather_code"],
        "timezone": "auto",
        "forecast_minutely_15": 4,  # 4 × 15-min slots = 1 hour; we use first 2
    }
    with httpx.Client(timeout=15) as client:
        resp = client.get(OPEN_METEO_FORECAST_URL, params=params)
        resp.raise_for_status()
    data = resp.json()
    minutely = data.get("minutely_15", {})
    times: list[str] = minutely.get("time", [])
    precip: list[float] = minutely.get("precipitation", [])

    # Build per-minute approximate entries (15-min slots → 15 minutes)
    entries = []
    for idx, (t, p) in enumerate(zip(times[:2], precip[:2])):
        for minute in range(idx * 15, min((idx + 1) * 15, 16)):
            entries.append({"minute_offset": minute, "precipitation_mm": round(p, 2)})

    # Natural-language summary
    first_rain_minute = None
    for entry in entries:
        if entry["precipitation_mm"] > 0.05:
            first_rain_minute = entry["minute_offset"]
            break

    if first_rain_minute is None:
        summary = "No precipitation expected in the next 15 minutes."
    elif first_rain_minute == 0:
        summary = "It is currently raining."
    else:
        summary = f"Rain expected to start in approximately {first_rain_minute} minutes."

    return {"location": location, "entries": entries[:16], "summary": summary}


def get_hourly_forecast(location: str, hours: int = 12) -> dict[str, Any]:
    """Return hourly forecast for the next N hours.

    Args:
        location: Human-readable location string.
        hours: Number of hours to forecast (default 12, max 48).

    Returns:
        Dictionary with hourly temperature, precipitation probability,
        wind, and humidity.
    """
    hours = max(1, min(hours, 48))
    lat, lon = geocode_location(location)
    temperature_unit = get_temperature_unit()
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "temperature_2m",
            "precipitation_probability",
            "precipitation",
            "wind_speed_10m",
            "relative_humidity_2m",
            "weather_code",
        ],
        "wind_speed_unit": "kmh",
        "temperature_unit": temperature_unit,
        "timezone": "auto",
        "forecast_hours": hours,
    }
    with httpx.Client(timeout=15) as client:
        resp = client.get(OPEN_METEO_FORECAST_URL, params=params)
        resp.raise_for_status()
    data = resp.json()
    hourly = data.get("hourly", {})
    times: list[str] = hourly.get("time", [])[:hours]
    temps: list[float] = hourly.get("temperature_2m", [])[:hours]
    precip_prob: list[float] = hourly.get("precipitation_probability", [])[:hours]
    precip: list[float] = hourly.get("precipitation", [])[:hours]
    wind: list[float] = hourly.get("wind_speed_10m", [])[:hours]
    humidity: list[float] = hourly.get("relative_humidity_2m", [])[:hours]
    codes: list[int] = hourly.get("weather_code", [])[:hours]

    entries = []
    for i, t in enumerate(times):
        code = codes[i] if i < len(codes) else 0
        entries.append(
            {
                "hour_offset": i,
                "time_local": t,
                "temperature_c": temps[i] if i < len(temps) else None,
                "precipitation_probability_pct": precip_prob[i] if i < len(precip_prob) else None,
                "precipitation_mm": precip[i] if i < len(precip) else None,
                "wind_speed_kmh": wind[i] if i < len(wind) else None,
                "humidity_pct": humidity[i] if i < len(humidity) else None,
                "weather_code": code,
                "weather_description": _wmo_desc(code),
            }
        )
    return {"location": location, "entries": entries, "temperature_unit": temperature_unit}


def get_daily_forecast(location: str, days: int = 7) -> dict[str, Any]:
    """Return daily forecast for the next N days.

    Args:
        location: Human-readable location string.
        days: Number of days to forecast (default 7, max 16).

    Returns:
        Dictionary with daily high/low temps, precipitation, UV index,
        sunrise/sunset, and dominant weather description.
    """
    days = max(1, min(days, 16))
    lat, lon = geocode_location(location)
    temperature_unit = get_temperature_unit()
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "uv_index_max",
            "sunrise",
            "sunset",
            "weather_code",
        ],
        "temperature_unit": temperature_unit,
        "timezone": "auto",
        "forecast_days": days,
    }
    with httpx.Client(timeout=15) as client:
        resp = client.get(OPEN_METEO_FORECAST_URL, params=params)
        resp.raise_for_status()
    data = resp.json()
    daily = data.get("daily", {})

    dates: list[str] = daily.get("time", [])[:days]
    temp_max: list[float] = daily.get("temperature_2m_max", [])[:days]
    temp_min: list[float] = daily.get("temperature_2m_min", [])[:days]
    precip_sum: list[float] = daily.get("precipitation_sum", [])[:days]
    uv: list[float] = daily.get("uv_index_max", [])[:days]
    sunrise: list[str] = daily.get("sunrise", [])[:days]
    sunset: list[str] = daily.get("sunset", [])[:days]
    codes: list[int] = daily.get("weather_code", [])[:days]

    entries = []
    for i, d in enumerate(dates):
        code = codes[i] if i < len(codes) else 0
        entries.append(
            {
                "day_offset": i,
                "date": d,
                "temp_max_c": temp_max[i] if i < len(temp_max) else None,
                "temp_min_c": temp_min[i] if i < len(temp_min) else None,
                "precipitation_sum_mm": precip_sum[i] if i < len(precip_sum) else None,
                "uv_index_max": uv[i] if i < len(uv) else None,
                "sunrise": sunrise[i] if i < len(sunrise) else None,
                "sunset": sunset[i] if i < len(sunset) else None,
                "weather_code": code,
                "weather_description": _wmo_desc(code),
            }
        )
    return {"location": location, "entries": entries, "temperature_unit": temperature_unit}
