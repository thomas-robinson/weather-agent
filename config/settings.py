"""Application-wide settings and constants."""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# NVIDIA NIM
# ---------------------------------------------------------------------------
NVIDIA_API_KEY: str = os.environ.get("NVIDIA_API_KEY", "")
NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
# Primary model — Nemotron Nano 8B for fast tool-routing and summarization.
NIM_MODEL: str = "nvidia/llama-3.1-nemotron-nano-8b-v1"
NIM_TEMPERATURE: float = 0.6
NIM_MAX_TOKENS: int = 4096

# ---------------------------------------------------------------------------
# Open-Meteo
# ---------------------------------------------------------------------------
OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
OPEN_METEO_FORECAST_URL: str = f"{OPEN_METEO_BASE_URL}/forecast"

# ---------------------------------------------------------------------------
# NWS
# ---------------------------------------------------------------------------
NWS_ALERTS_URL: str = "https://api.weather.gov/alerts/active"
NWS_POINTS_URL: str = "https://api.weather.gov/points"

# ---------------------------------------------------------------------------
# FAA
# ---------------------------------------------------------------------------
FAA_STATUS_URL: str = (
    "https://nasstatus.faa.gov/api/airport-status-information"
)

# ---------------------------------------------------------------------------
# WMO weather-code → description mapping (Open-Meteo uses WMO codes)
# ---------------------------------------------------------------------------
WMO_CODE_MAP: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}
