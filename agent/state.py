"""LangGraph agent state schema."""

from __future__ import annotations

from typing import Annotated, Any
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages

from models.schemas import UserProfile


class AgentState(TypedDict):
    """State passed between nodes in the LangGraph ReAct agent."""

    # Conversation history — new messages are appended via add_messages.
    messages: Annotated[list[Any], add_messages]

    # Persistent user profile updated during the session.
    user_profile: UserProfile

    # Scratch-pad for the most recent tool results (serialised as strings).
    tool_results: dict[str, Any]

    # Flag set when a morning briefing has been requested.
    morning_briefing_requested: bool

    # Required by langgraph's create_react_agent to limit tool-call loops.
    remaining_steps: int
