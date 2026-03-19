"""Response formatting helpers."""

from __future__ import annotations

from config.settings import WMO_CODE_MAP


def celsius_to_fahrenheit(c: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return c * 9 / 5 + 32


def format_temperature(c: float) -> str:
    """Return a human-readable temperature string showing both °C and °F."""
    f = celsius_to_fahrenheit(c)
    return f"{c:.1f}°C ({f:.1f}°F)"


def weather_code_description(code: int) -> str:
    """Return a human-readable description for a WMO weather code."""
    return WMO_CODE_MAP.get(code, f"Weather code {code}")


def format_wind(speed_kmh: float, direction_deg: float) -> str:
    """Return a human-readable wind description."""
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
    ]
    idx = int((direction_deg + 11.25) / 22.5) % 16
    cardinal = directions[idx]
    mph = speed_kmh * 0.621371
    return f"{speed_kmh:.1f} km/h ({mph:.1f} mph) from {cardinal}"


def format_precipitation(mm: float) -> str:
    """Return a human-readable precipitation amount."""
    inches = mm / 25.4
    return f"{mm:.1f} mm ({inches:.2f} in)"
