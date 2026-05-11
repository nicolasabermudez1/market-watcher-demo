"""Bootstrap the openai-agents SDK to talk to Gemini via its OpenAI-compatibility layer.

Gemini exposes an OpenAI-compatible endpoint at:
    https://generativelanguage.googleapis.com/v1beta/openai/

We construct an AsyncOpenAI client pointed at that URL with the user's Gemini key,
then register it as the default client for the agents SDK. Gemini does not support
OpenAI's newer Responses API, so we also force chat_completions.

Import this module BEFORE constructing any Agent — `market_watcher/__init__.py`
takes care of that.
"""

import os

from openai import AsyncOpenAI
from agents import (
    set_default_openai_client,
    set_default_openai_api,
    set_tracing_disabled,
)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def configure() -> None:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        # Defer the error to main.py / cli.py which shows a friendly banner.
        return

    # Belt-and-braces: also export OPENAI_* env vars so any OpenAI client created
    # by the agents SDK internally (bypassing set_default_openai_client) still
    # hits Gemini's endpoint instead of OpenAI's.
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = GEMINI_BASE_URL

    client = AsyncOpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)
    set_default_openai_client(client, use_for_tracing=False)
    set_default_openai_api("chat_completions")
    # OpenAI's tracing dashboard won't accept Gemini traffic — disable to silence warnings.
    set_tracing_disabled(True)
