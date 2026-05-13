"""Market Watcher — Streamlit entry point.
Run: uv run streamlit run src/market_watcher/main.py
"""

import os

import streamlit as st

# Page config must be first Streamlit call
st.set_page_config(
    page_title="Market Watcher — Centrica Procurement",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
from market_watcher.ui import tab_digest, tab_dashboard, tab_strategy, tab_category_placeholder
from market_watcher.tools.mock_services import get_categories

st.markdown(CENTRICA_CSS, unsafe_allow_html=True)

# Sidebar
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
    categories_meta = get_categories()
    live_count = sum(1 for c in categories_meta if c["status"] == "Live")
    pilot_count = sum(1 for c in categories_meta if c["status"] == "Pilot")
    st.markdown(f"**Categories tracked:** {len(categories_meta)}")
    st.markdown(f"&nbsp;&nbsp;&nbsp;✅ Live: {live_count}")
    st.markdown(f"&nbsp;&nbsp;&nbsp;🚀 Pilot: {pilot_count}")
    st.markdown(f"&nbsp;&nbsp;&nbsp;⏳ Coming soon: {len(categories_meta) - live_count - pilot_count}")
    total_spend = sum(c["spend_gbp_m"] for c in categories_meta)
    st.markdown(f"**Total spend covered:** £{total_spend:,.0f}m")
    st.markdown("---")
    st.caption("Powered by Google Gemini 2.5 · openai-agents SDK")


# ── Top-level CATEGORY tabs ──────────────────────────────────────────────────
tab_labels = [f"{c['icon']}  {c['name']}" for c in categories_meta]
cat_tabs = st.tabs(tab_labels)

for tab_obj, category in zip(cat_tabs, categories_meta):
    with tab_obj:
        if category["id"] == "it_software":
            # Full Market Watcher stack — 3 sub-tabs
            sub_tabs = st.tabs([
                "📋  Monday Digest",
                "📊  Category Dashboard",
                "📘  Category Strategy",
            ])
            with sub_tabs[0]:
                tab_digest.render()
            with sub_tabs[1]:
                tab_dashboard.render()
            with sub_tabs[2]:
                tab_strategy.render()
        else:
            tab_category_placeholder.render(category)
