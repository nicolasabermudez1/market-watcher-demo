"""Market Watcher — Centrica Procurement Intelligence Demo.

Importing this package configures the openai-agents SDK to use Gemini
via its OpenAI-compatibility endpoint.
"""

from market_watcher import config  # loads .env / st.secrets into os.environ
from market_watcher.llm_client import configure as _configure_llm

_configure_llm()
