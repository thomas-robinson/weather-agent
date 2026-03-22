"""Wardrobe and accessory recommendation tool — Nemotron-powered reasoning."""

from __future__ import annotations

import json
from typing import Any

from tools.weather import get_current_weather, get_hourly_forecast, get_daily_forecast, get_temperature_unit
from tools.alerts import get_weather_alerts
from agent.prompts import CLOTHING_REASONING_PROMPT


def get_clothing_recommendation(
    location: str,
    activities: list[str],
    style_preference: str = "casual",
    cold_sensitivity: str = "medium",
) -> dict[str, Any]:
    """Generate personalized clothing and accessory recommendations.

    Gathers current and forecast weather data for the location, then uses
    Nemotron (via the agent's LLM) to reason about appropriate clothing.

    Args:
        location: Human-readable location string.
        activities: List of planned activities (e.g. ["commute", "outdoor lunch"]).
        style_preference: User style — "casual", "business casual", "formal", "athletic".
        cold_sensitivity: User cold tolerance — "low", "medium", "high".

    Returns:
        Dictionary with recommended items, accessories, layers, and notes.
    """
    # Gather weather data
    unit_suffix = "°F" if get_temperature_unit() == "fahrenheit" else "°C"
    weather_parts: list[str] = []
    try:
        current = get_current_weather(location)
        weather_parts.append(
            f"Current: {current['weather_description']}, "
            f"temp {current['temperature_c']:.1f}{unit_suffix} "
            f"(feels like {current['feels_like_c']:.1f}{unit_suffix}), "
            f"humidity {current['humidity_pct']}%, "
            f"wind {current['wind_speed_kmh']:.1f} km/h, "
            f"UV index {current['uv_index']}"
        )
    except Exception as exc:
        weather_parts.append(f"Current weather unavailable: {exc}")
        current = {}

    try:
        hourly = get_hourly_forecast(location, hours=12)
        entries = hourly.get("entries", [])
        if entries:
            max_precip_prob = max(
                (e.get("precipitation_probability_pct") or 0) for e in entries
            )
            temp_range = (
                min(e.get("temperature_c") or 0 for e in entries),
                max(e.get("temperature_c") or 0 for e in entries),
            )
            weather_parts.append(
                f"Next 12 hours: temp range {temp_range[0]:.1f}–{temp_range[1]:.1f}{unit_suffix}, "
                f"max precipitation probability {max_precip_prob:.0f}%"
            )
    except Exception:
        pass

    try:
        daily = get_daily_forecast(location, days=1)
        entries = daily.get("entries", [])
        if entries:
            today = entries[0]
            weather_parts.append(
                f"Today's forecast: high {today.get('temp_max_c'):.1f}{unit_suffix}, "
                f"low {today.get('temp_min_c'):.1f}{unit_suffix}, "
                f"precipitation {today.get('precipitation_sum_mm'):.1f} mm, "
                f"UV max {today.get('uv_index_max'):.1f}"
            )
    except Exception:
        pass

    try:
        alerts = get_weather_alerts(location)
        if alerts.get("alerts"):
            events = [a["event"] for a in alerts["alerts"]]
            weather_parts.append(f"Active weather alerts: {', '.join(events)}")
    except Exception:
        pass

    weather_summary = "\n".join(weather_parts) if weather_parts else "No weather data available"

    # Use Nemotron to reason about clothing
    prompt = CLOTHING_REASONING_PROMPT.format(
        location=location,
        weather_data=weather_summary,
        cold_sensitivity=cold_sensitivity,
        style_preference=style_preference,
        activities=", ".join(activities) if activities else "general daily activities",
    )

    try:
        from agent.llm import llm as get_llm

        response = get_llm().invoke(prompt)
        recommendation_text = (
            response.content if hasattr(response, "content") else str(response)
        )
    except Exception as exc:
        recommendation_text = f"Could not generate AI recommendation: {exc}"

    # Extract structured items from the response (best-effort parsing)
    items, accessories, layers, notes = _parse_recommendation(recommendation_text)

    return {
        "location": location,
        "temperature_summary": weather_parts[0] if weather_parts else "",
        "items": items,
        "accessories": accessories,
        "layers": layers,
        "notes": notes,
        "full_recommendation": recommendation_text,
    }


def _parse_recommendation(text: str) -> tuple[list[str], list[str], list[str], str]:
    """Best-effort extraction of structured data from the LLM response text."""
    items: list[str] = []
    accessories: list[str] = []
    layers: list[str] = []
    notes: list[str] = []

    current_section: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(kw in lower for kw in ("clothing", "outfit", "wear", "items")):
            current_section = "items"
        elif any(kw in lower for kw in ("accessor",)):
            current_section = "accessories"
        elif any(kw in lower for kw in ("layer",)):
            current_section = "layers"
        elif any(kw in lower for kw in ("note", "tip", "reminder", "special")):
            current_section = "notes"
        elif stripped.startswith(("-", "•", "*", "·")) or (
            len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".)"
        ):
            content = stripped.lstrip("-•*·0123456789.) ").strip()
            if current_section == "accessories":
                accessories.append(content)
            elif current_section == "layers":
                layers.append(content)
            elif current_section == "notes":
                notes.append(content)
            else:
                items.append(content)

    return items, accessories, layers, "\n".join(notes)
