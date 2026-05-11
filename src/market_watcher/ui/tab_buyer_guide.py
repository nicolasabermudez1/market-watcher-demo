"""Tab 3 — Buyer Guide (conversational interface with live re-ranking)."""

import streamlit as st

from market_watcher.config import SPEND_THRESHOLD, DEMO_CATEGORY
from market_watcher.ui.styles import header_html
from market_watcher.ui.agent_theatre import stream

SUPPLIER_LOGOS = {
    "microsoft": "🔷", "sap": "🟦", "oracle": "🟥", "salesforce": "☁️",
    "servicenow": "🟢", "workday": "🟧", "atlassian": "🟦", "pega": "🟪",
    "snowflake": "❄️",
}

TIER_COLORS = {"Strategic": "#0F2067", "Preferred": "#9B2BF7", "Approved": "#B999F6"}


def render():
    st.markdown(header_html(
        "Buyer Guide — Self-Serve Buying",
        f"{DEMO_CATEGORY} · Purchases under £{SPEND_THRESHOLD:,} · Powered by PSL catalogue"
    ), unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### Ranking criteria")
        st.markdown("*Move a slider — ranking re-runs instantly*")
        weights = {
            "price": st.slider("💰 Price / Value", 0.0, 1.0, 0.20, 0.05, key="w_price"),
            "quality": st.slider("⭐ Quality / Reliability", 0.0, 1.0, 0.25, 0.05, key="w_quality"),
            "esg": st.slider("🌱 ESG / Sustainability", 0.0, 1.0, 0.15, 0.05, key="w_esg"),
            "delivery_speed": st.slider("⚡ Delivery speed", 0.0, 1.0, 0.10, 0.05, key="w_delivery"),
            "payment_terms": st.slider("📅 Payment terms", 0.0, 1.0, 0.10, 0.05, key="w_payment"),
            "support": st.slider("🤝 Support / SLA", 0.0, 1.0, 0.20, 0.05, key="w_support"),
        }
        total = sum(weights.values())
        st.caption(f"Total weight: {total:.2f} (will be normalised to 1.0)")

    col_rank, col_chat = st.columns([1, 1])

    with col_rank:
        st.subheader("🏆 Live PSL Ranking")
        _render_live_ranking(weights)

    with col_chat:
        st.subheader("💬 Ask the Buyer Guide")
        _render_chat()


def _render_live_ranking(weights: dict):
    try:
        from market_watcher.tools.mock_services import get_psl_search
        ranked = get_psl_search(category="IT Software", criteria_weights=weights)

        for s in ranked:
            rank = s["rank"]
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
            tier_color = TIER_COLORS.get(s.get("tier", ""), "#B999F6")
            logo = SUPPLIER_LOGOS.get(s["supplier_id"], "🔹")

            with st.container():
                st.markdown(
                    f"""<div style="border:1px solid #DECFFF;border-radius:8px;padding:10px 14px;margin-bottom:6px;background:#fafafa;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <span style="font-size:1.0rem;font-weight:bold;color:#0F2067;">{medal} {logo} {s['name']}</span>
                                <div style="font-size:0.75rem;color:#666;">{s.get('subcategory','')}</div>
                            </div>
                            <div style="text-align:right;">
                                <span style="background:{tier_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.7rem;">{s.get('tier', '')}</span>
                                <div style="font-size:1.2rem;font-weight:bold;color:#9B2BF7;margin-top:2px;">{s['weighted_score']:.2f}</div>
                            </div>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                with st.expander("Score breakdown · Risks · Contact"):
                    label_map = {"price": "💰 Price", "quality": "⭐ Quality", "esg": "🌱 ESG",
                                 "delivery_speed": "⚡ Speed", "payment_terms": "📅 Payment", "support": "🤝 Support"}
                    for k, v in s.get("scores", {}).items():
                        st.markdown(f"{label_map.get(k, k)}: **{v:.2f}**")
                        st.progress(v)
                    if s.get("high_risk_count"):
                        st.warning(f"⚠️ {s['high_risk_count']} HIGH-priority risk(s) on file — see Dashboard.")
                    st.caption(f"Contact: {s.get('contact', '')}")
    except Exception as e:
        st.error(f"Ranking error: {e}")


def _render_chat():
    if "buyer_messages" not in st.session_state:
        st.session_state["buyer_messages"] = []
        st.session_state["buyer_history"] = []

    for msg in st.session_state["buyer_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state["buyer_messages"]:
        st.markdown("**Try asking:**")
        suggestions = [
            "I need a CRM for our customer service team — ESG is the priority",
            "Find me an ITSM tool with strong support SLAs",
            "Compare SAP and Oracle on payment terms",
            "Which vendor has the best Gartner positioning for data?",
        ]
        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            if cols[i % 2].button(s, key=f"suggest_{i}", use_container_width=True):
                _push(s)
                st.rerun()

    if prompt := st.chat_input("Ask about vendors, pricing, ESG, certifications..."):
        _push(prompt)
        st.rerun()


def _push(message: str):
    st.session_state["buyer_messages"].append({"role": "user", "content": message})
    with st.chat_message("user"):
        st.markdown(message)
    with st.chat_message("assistant"):
        # Brief theatre for the chat (much shorter than the Monday scan)
        log_slot = st.empty()
        stream(track="ranking", message_delay=0.2, slot=log_slot)
        try:
            from market_watcher.subagents.query import run_buyer_query
            result = run_buyer_query(message, st.session_state.get("buyer_history", []))
            response = result.get("response", "Sorry — agent error.")
            if result.get("status") == "ok":
                st.session_state["buyer_history"] = result["history"]
        except Exception as e:
            response = f"Agent error: {e}"
        log_slot.empty()
        st.markdown(response)
        st.session_state["buyer_messages"].append({"role": "assistant", "content": response})
