"""Geocoding utilities using geopy."""

from __future__ import annotations

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

_geolocator = Nominatim(user_agent="weather-agent/1.0")


def geocode_location(location: str) -> tuple[float, float]:
    """Convert a location name to (latitude, longitude).

    Args:
        location: Human-readable location string (e.g. "Austin, TX").

    Returns:
        Tuple of (latitude, longitude) as floats.

    Raises:
        ValueError: If the location cannot be geocoded.
    """
    try:
        result = _geolocator.geocode(location, timeout=10)
    except (GeocoderTimedOut, GeocoderServiceError) as exc:
        raise ValueError(f"Geocoding service error for '{location}': {exc}") from exc

    if result is None:
        raise ValueError(f"Could not geocode location: '{location}'")

    return float(result.latitude), float(result.longitude)
