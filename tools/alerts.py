"""Weather alerts tool using the NWS API (US locations)."""

from __future__ import annotations

from typing import Any

import httpx

from config.settings import NWS_ALERTS_URL, NWS_POINTS_URL
from utils.geocoding import geocode_location


def _get_nws_zone(lat: float, lon: float, client: httpx.Client) -> str | None:
    """Return the NWS forecast zone ID for a lat/lon, or None on failure.

    Calls ``/points/{lat},{lon}`` and extracts the ``forecastZone`` field,
    e.g. ``https://api.weather.gov/zones/forecast/NJZ107`` → ``"NJZ107"``.
    Returns ``None`` for non-US locations (NWS returns 404) or on any
    network/parsing error.
    """
    try:
        url = f"{NWS_POINTS_URL}/{lat:.4f},{lon:.4f}"
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()
        zone_url: str = data.get("properties", {}).get("forecastZone", "")
        if zone_url:
            return zone_url.rstrip("/").split("/")[-1]
    except (httpx.HTTPStatusError, httpx.RequestError, KeyError, ValueError):
        pass
    return None


def get_weather_alerts(location: str) -> dict[str, Any]:
    """Return active weather alerts for a location.

    Uses the NWS API for US locations (free, no API key required).
    Falls back to an empty alert list for non-US locations or on any API
    error so that the agent never crashes due to alerts being unavailable.

    Args:
        location: Human-readable location string.

    Returns:
        Dictionary with a list of active alerts and their details.
    """
    lat, lon = geocode_location(location)

    alerts: list[dict[str, Any]] = []
    source = "NWS"

    try:
        with httpx.Client(timeout=15) as client:
            # Resolve the NWS forecast zone for this lat/lon first.
            # The /alerts/active endpoint does not reliably accept a raw
            # ``point`` parameter (the comma gets URL-encoded to %2C which
            # returns a 400), so we use the zone-based query instead.
            zone_id = _get_nws_zone(lat, lon, client)
            if not zone_id:
                # /points returned 404 (non-US location) or was unreachable.
                # There is no reliable fallback for non-US locations, so
                # return early with an empty alert list.
                source = "open-meteo (non-US location — NWS not available)"
                return {
                    "location": location,
                    "alerts": alerts,
                    "source": source,
                    "alert_count": 0,
                }
            params: dict[str, Any] = {
                "zone": zone_id,
                "status": "actual",
                "limit": 20,
            }
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
        status = exc.response.status_code
        if status == 404:
            # NWS returns 404 for non-US locations — treat as no alerts.
            source = "open-meteo (non-US location — NWS not available)"
        else:
            # Other HTTP errors (e.g. 400, 500) — degrade gracefully so the
            # agent can continue with the rest of the morning briefing.
            source = f"unavailable (NWS API error {status})"
    except Exception:
        source = "unavailable"

    return {
        "location": location,
        "alerts": alerts,
        "source": source,
        "alert_count": len(alerts),
    }
