import os
import tomllib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud secrets fallback: when running under Streamlit, secrets pasted
# in the Cloud UI appear in st.secrets. Promote them into os.environ so the rest
# of the codebase (CLI, agents, tests) reads them via os.environ uniformly.
try:
    import streamlit as _st
    for _key in ("GEMINI_API_KEY", "GEMINI_MODEL_PRIMARY", "GEMINI_MODEL_FAST",
                 "BRAVE_SEARCH_API_KEY"):
        if _key in _st.secrets and not os.environ.get(_key):
            os.environ[_key] = str(_st.secrets[_key])
except Exception:
    pass

ROOT = Path(__file__).parent.parent.parent  # market-watcher-demo/

with open(ROOT / "config.toml", "rb") as f:
    _cfg = tomllib.load(f)

GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

MODEL_PRIMARY: str = os.environ.get("GEMINI_MODEL_PRIMARY", _cfg["models"]["primary"])
MODEL_FAST: str = os.environ.get("GEMINI_MODEL_FAST", _cfg["models"]["fast"])
MODEL_EMBEDDING: str = _cfg["models"]["embedding"]

USE_WEB_SEARCH: bool = _cfg["tools"]["use_web_search"]
USE_CHROMA: bool = _cfg["tools"]["use_chroma"]
USE_BRAVE_FALLBACK: bool = _cfg["tools"]["use_brave_fallback"]
BRAVE_API_KEY: str = os.environ.get("BRAVE_SEARCH_API_KEY", "")

DEMO_CATEGORY: str = _cfg["demo"]["category"]
DEMO_SUPPLIERS: list[str] = _cfg["demo"]["suppliers"]
SPEND_THRESHOLD: int = _cfg["demo"]["spend_threshold_gbp"]

FIXTURES_DIR = ROOT / _cfg["paths"]["fixtures"]
RUNS_DIR = ROOT / _cfg["paths"]["runs"]
OUTPUTS_DIR = ROOT / _cfg["paths"]["outputs"]
STATE_DB = ROOT / _cfg["paths"]["state_db"]

LOG_LEVEL: str = os.environ.get("DEMO_LOG_LEVEL", "INFO")

CENTRICA_NAVY = "#0F2067"
CENTRICA_MINT = "#85DB9C"
CENTRICA_LAVENDER = "#B999F6"
CENTRICA_PALE_LAV = "#DECFFF"
CENTRICA_PURPLE = "#9B2BF7"
