"""Weather alerts tool using the NWS API (US locations)."""

from __future__ import annotations

from typing import Any

import httpx

from config.settings import NWS_ALERTS_URL
from utils.geocoding import geocode_location


def get_weather_alerts(location: str) -> dict[str, Any]:
    """Return active weather alerts for a location.

    Uses the NWS API for US locations (free, no API key required).
    Falls back to an empty alert list for non-US locations.

    Args:
        location: Human-readable location string.

    Returns:
        Dictionary with a list of active alerts and their details.
    """
    lat, lon = geocode_location(location)

    alerts: list[dict[str, Any]] = []
    source = "NWS"

    try:
        params = {"point": f"{lat:.4f},{lon:.4f}", "status": "actual", "limit": 20}
        with httpx.Client(timeout=15) as client:
            resp = client.get(NWS_ALERTS_URL, params=params)
            resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        for feature in features:
            props = feature.get("properties", {})
            alerts.append(
                {
                    "event": props.get("event", "Unknown"),
                    "severity": props.get("severity", "Unknown"),
                    "headline": props.get("headline", ""),
                    "description": props.get("description", "")[:500],
                    "effective": props.get("effective", ""),
                    "expires": props.get("expires", ""),
                    "area": props.get("areaDesc", ""),
                }
            )
    except httpx.HTTPStatusError as exc:
        # NWS returns 404 for non-US locations — treat as no alerts.
        if exc.response.status_code == 404:
            source = "open-meteo (non-US location — NWS not available)"
        else:
            raise
    except Exception:
        source = "unavailable"

    return {
        "location": location,
        "alerts": alerts,
        "source": source,
        "alert_count": len(alerts),
    }
