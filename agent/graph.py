"""LangGraph ReAct agent for the Personal Meteorologist (Storm).

Architecture
------------
The agent uses a standard LangGraph ``create_react_agent`` pattern:

1. The LLM (Nemotron via NIM) receives the conversation + available tools.
2. If Nemotron decides to call a tool, control flows to the tool node.
3. Tool results are added to the message history.
4. The loop continues until Nemotron produces a final answer.

The ``build_graph()`` function returns a compiled LangGraph that can be
invoked with an ``AgentState`` dict.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from agent.llm import llm
from agent.prompts import SYSTEM_PROMPT
from agent.state import AgentState
from tools.weather import (
    get_current_weather as _get_current_weather,
    get_15min_nowcast as _get_15min_nowcast,
    get_hourly_forecast as _get_hourly_forecast,
    get_daily_forecast as _get_daily_forecast,
)
from tools.alerts import get_weather_alerts as _get_weather_alerts
from tools.airport import get_airport_delays as _get_airport_delays
from tools.routing import get_route_weather as _get_route_weather
from tools.clothing import get_clothing_recommendation as _get_clothing_recommendation


# ---------------------------------------------------------------------------
# LangChain @tool wrappers — these give Nemotron typed descriptions it can
# use for function-calling.
# ---------------------------------------------------------------------------


@tool
def get_current_weather(location: str) -> dict:
    """Get current weather conditions (temperature, humidity, wind, UV index,
    feels-like temperature, and weather description) for a location.

    Args:
        location: Human-readable location name, e.g. "Austin, TX".
    """
    return _get_current_weather(location)


@tool
def get_15min_nowcast(location: str) -> dict:
    """Get minute-by-minute precipitation nowcast for the next 15 minutes.
    Returns a natural-language summary like 'Rain starts in 8 minutes'.

    Args:
        location: Human-readable location name.
    """
    return _get_15min_nowcast(location)


@tool
def get_hourly_forecast(location: str, hours: int = 12) -> dict:
    """Get hourly weather forecast for the next N hours (default 12).
    Includes temperature, precipitation probability, wind, and humidity.

    Args:
        location: Human-readable location name.
        hours: Number of hours to forecast (1–48).
    """
    return _get_hourly_forecast(location, hours)


@tool
def get_daily_forecast(location: str, days: int = 7) -> dict:
    """Get daily weather forecast for the next N days (default 7).
    Includes high/low temperature, precipitation, UV index, sunrise/sunset.

    Args:
        location: Human-readable location name.
        days: Number of days to forecast (1–16).
    """
    return _get_daily_forecast(location, days)


@tool
def get_weather_alerts(location: str) -> dict:
    """Get active weather alerts (flood warnings, severe thunderstorm watches,
    tornado watches, etc.) for a location using the NWS API.

    Args:
        location: Human-readable location name.
    """
    return _get_weather_alerts(location)


@tool
def get_airport_delays(airport_code: str) -> dict:
    """Get current airport delay information from the FAA Status API,
    including delay type, average delay minutes, and reason.
    Also returns a weather summary for the airport.

    Args:
        airport_code: IATA airport code, e.g. "DFW" or "LAX".
    """
    return _get_airport_delays(airport_code)


@tool
def get_route_weather(origin: str, destination: str) -> dict:
    """Get weather conditions and alerts along a driving route.
    Returns weather at origin, midpoint, and destination, plus any severe
    weather alerts along the route and a travel recommendation.

    Args:
        origin: Starting location string.
        destination: Ending location string.
    """
    return _get_route_weather(origin, destination)


@tool
def get_clothing_recommendation(
    location: str,
    activities: list[str],
    style_preference: str = "casual",
    cold_sensitivity: str = "medium",
) -> dict:
    """Get personalized clothing and accessory recommendations based on
    current and forecast weather conditions for a location.

    Args:
        location: Human-readable location name.
        activities: List of planned activities, e.g. ["commute", "outdoor lunch"].
        style_preference: User style — "casual", "business casual", "formal", "athletic".
        cold_sensitivity: Cold tolerance — "low", "medium", "high".
    """
    return _get_clothing_recommendation(location, activities, style_preference, cold_sensitivity)


TOOLS = [
    get_current_weather,
    get_15min_nowcast,
    get_hourly_forecast,
    get_daily_forecast,
    get_weather_alerts,
    get_airport_delays,
    get_route_weather,
    get_clothing_recommendation,
]


def build_graph():
    """Build and return the compiled LangGraph ReAct agent.

    The graph uses ``create_react_agent`` which implements the standard
    LangGraph ReAct pattern:
    - LLM node (Nemotron) decides on tool calls
    - Tool node executes the called tools
    - Loop continues until Nemotron produces a final answer

    Returns:
        A compiled LangGraph runnable that accepts an ``AgentState`` dict.
    """
    model = llm()
    graph = create_react_agent(
        model,
        tools=TOOLS,
        state_schema=AgentState,
        prompt=SYSTEM_PROMPT,
    )
    return graph


def build_morning_briefing_graph():
    """Build a graph configured for the morning briefing workflow.

    Uses the same ReAct agent but the caller injects a morning-briefing
    system message to trigger the full briefing workflow.
    """
    return build_graph()
