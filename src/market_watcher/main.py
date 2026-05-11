"""Market Watcher — Streamlit entry point.
Run: uv run streamlit run src/market_watcher/main.py
"""

import os
import sys
from pathlib import Path

import streamlit as st

# Page config must be first Streamlit call
st.set_page_config(
    page_title="Market Watcher — Centrica Procurement",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Check for API key before anything else
from dotenv import load_dotenv
load_dotenv()

from market_watcher import config as _cfg  # noqa: F401 — triggers Gemini client setup
if not os.environ.get("GEMINI_API_KEY"):
    st.error(
        "**GEMINI_API_KEY not set.**\n\n"
        "Get a free key from https://aistudio.google.com/apikey, then either:\n\n"
        "- **Local:** copy `.env.example` to `.env` and paste your key as `GEMINI_API_KEY=AIzaSy...`\n"
        "- **Streamlit Cloud:** paste it into App Settings → Secrets as `GEMINI_API_KEY = \"AIzaSy...\"`"
    )
    st.stop()

# Build Chroma index on startup (in-memory, fast)
try:
    from market_watcher.tools.retrieval import build_index
    if "chroma_built" not in st.session_state:
        build_index()
        st.session_state["chroma_built"] = True
except Exception as e:
    st.warning(f"Vector index unavailable (non-critical): {e}")

from market_watcher.ui.styles import CENTRICA_CSS
from market_watcher.ui import tab_digest, tab_dashboard, tab_buyer_guide

# Inject brand CSS
st.markdown(CENTRICA_CSS, unsafe_allow_html=True)

# Sidebar branding
with st.sidebar:
    st.markdown(
        """<div style="text-align:center;padding:1rem 0;">
            <div style="font-family:Arial,sans-serif;font-size:1.4rem;font-weight:bold;color:#85DB9C;">
                Market Watcher
            </div>
            <div style="font-size:0.75rem;color:#DECFFF;margin-top:4px;">
                Centrica Procurement Intelligence
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("**Category:** IT Software")
    st.markdown("**Vendors:** Microsoft · SAP · Oracle · Salesforce · ServiceNow · Workday · Atlassian · Pega · Snowflake")
    st.markdown("**Mode:** Mock presentation demo")
    st.markdown("---")
    st.caption("Powered by Google Gemini 2.5 · openai-agents SDK")

# Main tabs
tab1, tab2, tab3 = st.tabs([
    "📋  Monday Digest",
    "📊  Supplier Dashboard",
    "🛒  Buyer Guide",
])

with tab1:
    tab_digest.render()

with tab2:
    tab_dashboard.render()

with tab3:
    tab_buyer_guide.render()
