"""NVIDIA NIM LLM configuration using langchain-nvidia-ai-endpoints."""

from __future__ import annotations

import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from config.settings import (
    NVIDIA_API_KEY,
    NIM_BASE_URL,
    NIM_MODEL,
    NIM_TEMPERATURE,
    NIM_MAX_TOKENS,
)


def get_llm() -> ChatNVIDIA:
    """Return a configured ChatNVIDIA instance pointed at the NIM endpoint.

    The NVIDIA_API_KEY environment variable must be set before calling this
    function (or set in a .env file loaded via python-dotenv).
    """
    api_key = NVIDIA_API_KEY or os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "NVIDIA_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )

    return ChatNVIDIA(
        model=NIM_MODEL,
        api_key=api_key,
        base_url=NIM_BASE_URL,
        temperature=NIM_TEMPERATURE,
        max_tokens=NIM_MAX_TOKENS,
    )


# Module-level singleton — lazily created to avoid import-time errors when
# the API key is not yet configured.
_llm: ChatNVIDIA | None = None


def llm() -> ChatNVIDIA:
    """Return the module-level LLM singleton, creating it on first call."""
    global _llm
    if _llm is None:
        _llm = get_llm()
    return _llm
