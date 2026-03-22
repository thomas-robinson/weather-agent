"""Pydantic schemas for all data models used by the weather agent."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """Persistent user profile stored in session state."""

    name: str = ""
    default_location: str = ""
    commute_mode: str = "driving"  # driving, walking, cycling, transit
    cold_sensitivity: str = "medium"  # low, medium, high
    style_preference: str = "casual"  # casual, business casual, formal, athletic
    activities_today: list[str] = Field(default_factory=list)
    flight_info: dict[str, Any] = Field(default_factory=dict)
    temperature_unit: str = "fahrenheit"  # "fahrenheit" or "celsius"


class CurrentWeather(BaseModel):
    """Current weather conditions for a location."""

    location: str
    latitude: float
    longitude: float
    temperature_c: float
    feels_like_c: float
    humidity_pct: float
    wind_speed_kmh: float
    wind_direction_deg: float
    precipitation_mm: float
    weather_code: int
    weather_description: str
    uv_index: float
    timestamp: str


class NowcastEntry(BaseModel):
    """Single minute entry in a 15-minute precipitation nowcast."""

    minute_offset: int
    precipitation_mm: float


class NowcastResult(BaseModel):
    """15-minute minute-by-minute precipitation nowcast."""

    location: str
    entries: list[NowcastEntry]
    summary: str  # e.g. "Rain starts in 8 minutes"


class HourlyEntry(BaseModel):
    """Single hour in an hourly forecast."""

    hour_offset: int
    time_local: str
    temperature_c: float
    precipitation_probability_pct: float
    precipitation_mm: float
    wind_speed_kmh: float
    humidity_pct: float
    weather_code: int
    weather_description: str


class HourlyForecast(BaseModel):
    """Hourly forecast for a location."""

    location: str
    entries: list[HourlyEntry]


class DailyEntry(BaseModel):
    """Single day in a daily forecast."""

    day_offset: int
    date: str
    temp_max_c: float
    temp_min_c: float
    precipitation_sum_mm: float
    uv_index_max: float
    sunrise: str
    sunset: str
    weather_code: int
    weather_description: str


class DailyForecast(BaseModel):
    """Daily forecast for a location."""

    location: str
    entries: list[DailyEntry]


class WeatherAlert(BaseModel):
    """A single weather alert/warning."""

    event: str
    severity: str
    headline: str
    description: str
    effective: str
    expires: str
    area: str


class WeatherAlerts(BaseModel):
    """Collection of active weather alerts for a location."""

    location: str
    alerts: list[WeatherAlert]
    source: str  # "NWS" or "open-meteo"


class AirportDelay(BaseModel):
    """Airport delay information from FAA."""

    airport_code: str
    airport_name: str
    delay_status: bool
    delay_type: str  # ground_delay, ground_stop, none, etc.
    average_delay_minutes: int
    reason: str
    weather_summary: str


class RouteWeather(BaseModel):
    """Weather conditions and alerts along a route."""

    origin: str
    destination: str
    origin_weather_summary: str
    destination_weather_summary: str
    alerts_along_route: list[str]
    recommendation: str
    safe_to_travel: bool


class ClothingRecommendation(BaseModel):
    """Personalized clothing and accessory recommendations."""

    location: str
    temperature_summary: str
    items: list[str]
    accessories: list[str]
    layers: list[str]
    notes: str
