"""Personal Meteorologist AI Agent — Gradio UI.

Run with:
    python app.py

Environment variable required:
    NVIDIA_API_KEY   — NVIDIA NIM API key from build.nvidia.com
"""

from __future__ import annotations

import json
import os
from typing import Any, Generator

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from agent.graph import build_graph
from agent.prompts import MORNING_BRIEFING_PROMPT
from models.schemas import UserProfile

# ---------------------------------------------------------------------------
# Error classification helpers
# ---------------------------------------------------------------------------

_AUTH_ERROR_KEYWORDS = ("api key", "apikey", "401", "unauthorized", "authentication", "forbidden", "nvapi")

# ---------------------------------------------------------------------------
# Build the LangGraph agent (compiled once at startup)
# ---------------------------------------------------------------------------
_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


# ---------------------------------------------------------------------------
# Chat logic
# ---------------------------------------------------------------------------

def _profile_from_ui(
    name: str,
    location: str,
    commute: str,
    cold_sens: str,
    style: str,
    activities: str,
    airport_code: str,
    flight_time: str,
) -> UserProfile:
    """Build a UserProfile from sidebar UI fields."""
    flight_info: dict[str, str] = {}
    if airport_code:
        flight_info["airport_code"] = airport_code.upper().strip()
    if flight_time:
        flight_info["flight_time"] = flight_time

    return UserProfile(
        name=name.strip() or "Friend",
        default_location=location.strip(),
        commute_mode=commute,
        cold_sensitivity=cold_sens,
        style_preference=style,
        activities_today=[a.strip() for a in activities.split(",") if a.strip()],
        flight_info=flight_info,
    )


def chat(
    message: str,
    history: list[dict[str, str]],
    name: str,
    location: str,
    commute: str,
    cold_sens: str,
    style: str,
    activities: str,
    airport_code: str,
    flight_time: str,
) -> Generator[tuple[list[dict[str, str]], str], None, None]:
    """Process a user message and stream the agent's response."""
    profile = _profile_from_ui(
        name, location, commute, cold_sens, style, activities, airport_code, flight_time
    )

    # Build LangGraph input
    from langchain_core.messages import HumanMessage

    state: dict[str, Any] = {
        "messages": [HumanMessage(content=message)],
        "user_profile": profile,
        "tool_results": {},
        "morning_briefing_requested": False,
        "remaining_steps": 25,
    }

    # Prepend conversation history as messages
    if history:
        from langchain_core.messages import AIMessage, HumanMessage as HM
        prior: list[Any] = []
        for turn in history:
            if turn.get("role") == "user":
                prior.append(HM(content=turn["content"]))
            elif turn.get("role") == "assistant":
                prior.append(AIMessage(content=turn["content"]))
        state["messages"] = prior + state["messages"]

    tool_calls_display: list[str] = []
    final_answer = ""

    try:
        graph = _get_graph()
        # Stream events so we can surface tool calls to the UI in real-time
        for event in graph.stream(state, stream_mode="values"):
            messages = event.get("messages", [])
            if not messages:
                continue
            last = messages[-1]
            msg_type = type(last).__name__

            if msg_type == "AIMessage":
                # Check for tool calls — yield intermediate reasoning update
                if hasattr(last, "tool_calls") and last.tool_calls:
                    for tc in last.tool_calls:
                        tool_name = tc.get("name", "unknown_tool")
                        tool_args = tc.get("args", {})
                        tool_calls_display.append(
                            f"🔧 **Calling `{tool_name}`** with: `{json.dumps(tool_args)}`"
                        )
                    thinking_display = "\n\n".join(tool_calls_display)
                    partial_answer = f"*Reasoning…*\n\n{thinking_display}"
                    yield history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": partial_answer},
                    ], ""
                if last.content:
                    final_answer = last.content

            elif msg_type == "ToolMessage":
                tool_name = getattr(last, "name", "tool")
                tool_calls_display.append(
                    f"✅ **`{tool_name}` returned** — data received"
                )
                # Yield updated reasoning so the user sees each tool result as it arrives
                thinking_display = "\n\n".join(tool_calls_display)
                partial_answer = f"*Reasoning…*\n\n{thinking_display}"
                yield history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": partial_answer},
                ], ""

        # Build the final answer, prepending the reasoning trace if any tools were called
        thinking_display = "\n\n".join(tool_calls_display) if tool_calls_display else ""
        if thinking_display:
            partial_answer = f"*Reasoning…*\n\n{thinking_display}\n\n---\n\n{final_answer}"
        else:
            partial_answer = final_answer

    except Exception as exc:
        err_str = str(exc)
        if any(kw in err_str.lower() for kw in _AUTH_ERROR_KEYWORDS):
            final_answer = f"⚠️ Agent error: {exc}\n\nPlease check that your `NVIDIA_API_KEY` is set correctly."
        else:
            final_answer = f"⚠️ Agent error: {exc}"
        partial_answer = final_answer

    # Return updated history with the final answer
    updated_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": partial_answer},
    ]
    yield updated_history, ""


def morning_briefing(
    history: list[dict[str, str]],
    name: str,
    location: str,
    commute: str,
    cold_sens: str,
    style: str,
    activities: str,
    airport_code: str,
    flight_time: str,
) -> Generator[tuple[list[dict[str, str]], str], None, None]:
    """Trigger the full morning briefing workflow."""
    profile = _profile_from_ui(
        name, location, commute, cold_sens, style, activities, airport_code, flight_time
    )

    if not profile.default_location:
        updated_history = history + [
            {"role": "assistant", "content": "⚠️ Please set your **Default Location** in the sidebar before requesting a Morning Briefing!"}
        ]
        yield updated_history, ""
        return

    briefing_prompt = MORNING_BRIEFING_PROMPT.format(
        name=profile.name,
        location=profile.default_location,
        flight_info=json.dumps(profile.flight_info) if profile.flight_info else "none",
        style_preference=profile.style_preference,
        cold_sensitivity=profile.cold_sensitivity,
        commute_mode=profile.commute_mode,
    )

    # Reuse the chat generator with the synthetic briefing message
    yield from chat(
        briefing_prompt,
        history,
        name,
        location,
        commute,
        cold_sens,
        style,
        activities,
        airport_code,
        flight_time,
    )


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

THEME = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
)

CSS = """
.chat-container { height: 520px; overflow-y: auto; }
.tool-call { background: #1e293b; color: #94a3b8; border-radius: 8px; padding: 8px 12px; font-size: 0.85em; }
.sidebar-header { font-weight: 700; color: #1e40af; }
footer { display: none !important; }
"""

BANNER = """
<div style="background: linear-gradient(135deg, #1e40af 0%, #0369a1 100%); color: white;
            padding: 18px 24px; border-radius: 12px; margin-bottom: 16px;">
  <h1 style="margin:0; font-size: 1.8em;">⛅ Storm — Personal Meteorologist</h1>
  <p style="margin: 6px 0 0; opacity: 0.85;">
    Powered by NVIDIA Nemotron &amp; LangGraph ReAct Agent
  </p>
</div>
"""

INTRO_MESSAGE = (
    "Hi there! I'm **Storm** ⛅, your personal AI meteorologist powered by NVIDIA Nemotron.\n\n"
    "I can help you with:\n"
    "- 🌡️ Current weather conditions\n"
    "- 🌧️ 15-minute precipitation nowcasts\n"
    "- 📅 Hourly and daily forecasts\n"
    "- ⚠️ Severe weather alerts\n"
    "- ✈️ Airport delay predictions\n"
    "- 🗺️ Route weather & flood avoidance\n"
    "- 👗 Personalized clothing recommendations\n\n"
    "Fill in your profile in the sidebar, then ask me anything — or click **☀️ Morning Briefing** for a full daily overview!"
)

with gr.Blocks(title="Storm — Personal Meteorologist") as demo:
    gr.HTML(BANNER)

    with gr.Row():
        # ---- Sidebar -------------------------------------------------------
        with gr.Column(scale=1, min_width=260):
            gr.Markdown("### 👤 Your Profile", elem_classes=["sidebar-header"])

            name_input = gr.Textbox(label="Your Name", placeholder="e.g. Alex", value="")
            location_input = gr.Textbox(
                label="Default Location", placeholder="e.g. Austin, TX", value=""
            )
            commute_input = gr.Dropdown(
                label="Commute Mode",
                choices=["driving", "walking", "cycling", "transit"],
                value="driving",
            )
            cold_input = gr.Dropdown(
                label="Cold Sensitivity",
                choices=["low", "medium", "high"],
                value="medium",
            )
            style_input = gr.Dropdown(
                label="Style Preference",
                choices=["casual", "business casual", "formal", "athletic"],
                value="casual",
            )
            activities_input = gr.Textbox(
                label="Activities Today (comma-separated)",
                placeholder="e.g. commute, outdoor lunch, gym",
                value="",
            )

            gr.Markdown("### ✈️ Flight Info (optional)")
            airport_input = gr.Textbox(
                label="Airport Code", placeholder="e.g. DFW", value=""
            )
            flight_time_input = gr.Textbox(
                label="Flight Time", placeholder="e.g. 3:45 PM", value=""
            )

            morning_btn = gr.Button("☀️ Morning Briefing", variant="primary", size="lg")

        # ---- Chat area -----------------------------------------------------
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                value=[{"role": "assistant", "content": INTRO_MESSAGE}],
                label="Storm",
                height=520,
                avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=storm"),
            )
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask Storm about weather, airport delays, or what to wear…",
                    label="",
                    scale=9,
                    container=False,
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)

            gr.Examples(
                examples=[
                    "What's the weather like in New York right now?",
                    "Will it rain in the next 15 minutes in Seattle?",
                    "Give me the 7-day forecast for Miami.",
                    "Are there any weather alerts for Houston, TX?",
                    "What are the delays at LAX airport?",
                    "Is it safe to drive from Austin to Dallas today?",
                    "What should I wear today in Chicago? I have a business meeting.",
                ],
                inputs=msg_input,
                label="Try these questions:",
            )

    # ---- Profile inputs list (for easy passing to callbacks)
    profile_inputs = [
        name_input,
        location_input,
        commute_input,
        cold_input,
        style_input,
        activities_input,
        airport_input,
        flight_time_input,
    ]

    # ---- Wire up send button and Enter key
    send_btn.click(
        fn=chat,
        inputs=[msg_input, chatbot] + profile_inputs,
        outputs=[chatbot, msg_input],
    )
    msg_input.submit(
        fn=chat,
        inputs=[msg_input, chatbot] + profile_inputs,
        outputs=[chatbot, msg_input],
    )

    # ---- Morning briefing button
    morning_btn.click(
        fn=morning_briefing,
        inputs=[chatbot] + profile_inputs,
        outputs=[chatbot, msg_input],
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    _title = "🌦️  Storm — Personal Meteorologist AI Agent"
    _sep = "━" * len(_title)
    print(_title)
    print(_sep)
    print(f"👉 Open your browser to: http://localhost:{port}")
    print("   Press Ctrl+C to stop the server.")
    print(_sep)
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        theme=THEME,
        css=CSS,
    )
