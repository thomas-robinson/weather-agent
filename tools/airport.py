"""Airport delay tools using the FAA Airport Status API."""

from __future__ import annotations

from typing import Any

import httpx

from config.settings import FAA_STATUS_URL
from tools.weather import get_current_weather


def get_airport_delays(airport_code: str) -> dict[str, Any]:
    """Return delay information for an airport from the FAA Status API.

    Also fetches current weather at the airport location for context.

    Args:
        airport_code: IATA or ICAO airport code (e.g. "DFW", "LAX").

    Returns:
        Dictionary with delay status, type, average delay time, reason,
        and a brief weather summary.
    """
    airport_code = airport_code.upper().strip()

    delay_info: dict[str, Any] = {
        "airport_code": airport_code,
        "airport_name": "",
        "delay_status": False,
        "delay_type": "none",
        "average_delay_minutes": 0,
        "reason": "No delays reported",
        "weather_summary": "",
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(FAA_STATUS_URL)
            resp.raise_for_status()
        data = resp.json()

        # The FAA endpoint returns a list of programs (delay types)
        programs = data if isinstance(data, list) else []
        for program in programs:
            affected_airports = program.get("Airports", {}).get("Airport", [])
            if isinstance(affected_airports, dict):
                affected_airports = [affected_airports]
            for airport in affected_airports:
                if airport.get("@ARPT", "").upper() == airport_code:
                    delay_info["delay_status"] = True
                    delay_info["airport_name"] = airport.get("@ARPT", airport_code)
                    delay_info["delay_type"] = program.get("@Type", "unknown")
                    delay_info["average_delay_minutes"] = _parse_delay_minutes(
                        airport.get("Avg", "0")
                    )
                    delay_info["reason"] = airport.get("Reason", "Weather or traffic")
                    break
    except Exception as exc:
        delay_info["reason"] = f"FAA API unavailable: {exc}"

    # Fetch airport weather for correlation
    try:
        wx = get_current_weather(f"{airport_code} airport")
        delay_info["weather_summary"] = (
            f"{wx['weather_description']}, "
            f"{wx['temperature_c']:.1f}°C, "
            f"wind {wx['wind_speed_kmh']:.1f} km/h"
        )
    except Exception:
        delay_info["weather_summary"] = "Weather data unavailable"

    return delay_info


def _parse_delay_minutes(value: str) -> int:
    """Parse delay value like '45 minutes' or '1:15' into total minutes."""
    value = str(value).strip()
    if ":" in value:
        parts = value.split(":")
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except (ValueError, IndexError):
            return 0
    # Strip non-numeric characters
    digits = "".join(c for c in value if c.isdigit())
    return int(digits) if digits else 0
