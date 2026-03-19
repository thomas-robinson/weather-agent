"""Route weather analysis tool."""

from __future__ import annotations

from typing import Any

from tools.weather import get_current_weather
from tools.alerts import get_weather_alerts
from utils.geocoding import geocode_location


def get_route_weather(origin: str, destination: str) -> dict[str, Any]:
    """Return weather conditions and alerts along a driving route.

    Queries weather and NWS alerts for the origin, destination, and an
    approximate midpoint. Nemotron reasons about whether the route passes
    through severe weather zones.

    Args:
        origin: Starting location string.
        destination: Ending location string.

    Returns:
        Dictionary with weather summaries, alerts along the route,
        a recommendation, and a safe-to-travel flag.
    """
    # Gather data for origin, destination, and midpoint
    lat1, lon1 = geocode_location(origin)
    lat2, lon2 = geocode_location(destination)
    mid_lat = (lat1 + lat2) / 2
    mid_lon = (lon1 + lon2) / 2
    midpoint = f"{mid_lat:.4f},{mid_lon:.4f}"

    results: dict[str, Any] = {
        "origin": origin,
        "destination": destination,
        "origin_weather_summary": "",
        "destination_weather_summary": "",
        "midpoint_weather_summary": "",
        "alerts_along_route": [],
        "recommendation": "",
        "safe_to_travel": True,
    }

    # Origin weather
    try:
        wx_origin = get_current_weather(origin)
        results["origin_weather_summary"] = (
            f"{wx_origin['weather_description']}, "
            f"{wx_origin['temperature_c']:.1f}°C, "
            f"wind {wx_origin['wind_speed_kmh']:.1f} km/h"
        )
    except Exception as exc:
        results["origin_weather_summary"] = f"Unavailable ({exc})"

    # Destination weather
    try:
        wx_dest = get_current_weather(destination)
        results["destination_weather_summary"] = (
            f"{wx_dest['weather_description']}, "
            f"{wx_dest['temperature_c']:.1f}°C, "
            f"wind {wx_dest['wind_speed_kmh']:.1f} km/h"
        )
    except Exception as exc:
        results["destination_weather_summary"] = f"Unavailable ({exc})"

    # Midpoint weather
    try:
        wx_mid = get_current_weather(midpoint)
        results["midpoint_weather_summary"] = (
            f"{wx_mid['weather_description']}, "
            f"{wx_mid['temperature_c']:.1f}°C"
        )
    except Exception:
        results["midpoint_weather_summary"] = "Unavailable"

    # Alerts at each waypoint
    severe_keywords = {
        "tornado", "hurricane", "flood", "blizzard", "ice storm",
        "severe thunderstorm", "winter storm", "high wind",
    }
    for waypoint_name, waypoint_loc in [
        ("origin", origin),
        ("midpoint", midpoint),
        ("destination", destination),
    ]:
        try:
            alert_data = get_weather_alerts(waypoint_loc)
            for alert in alert_data.get("alerts", []):
                event = alert.get("event", "").lower()
                headline = alert.get("headline", "")
                if headline:
                    results["alerts_along_route"].append(
                        f"[{waypoint_name.capitalize()}] {headline}"
                    )
                    # Mark unsafe if severe keyword found
                    if any(kw in event for kw in severe_keywords):
                        results["safe_to_travel"] = False
        except Exception:
            pass

    # Build recommendation
    if not results["safe_to_travel"]:
        results["recommendation"] = (
            "⚠️ Severe weather alerts are active along this route. "
            "Consider delaying travel or using an alternate route. "
            "Check local authorities for road closures."
        )
    elif results["alerts_along_route"]:
        results["recommendation"] = (
            "Some weather alerts exist along the route. "
            "Travel with caution and monitor conditions. "
            "Allow extra time."
        )
    else:
        results["recommendation"] = (
            "No severe weather alerts along the route. "
            "Travel conditions appear normal — adjust your driving to match road conditions."
        )

    return results
