"""Tab 3 — Buyer Guide (conversational interface with live re-ranking)."""

import json
import time

import streamlit as st

from market_watcher.config import SPEND_THRESHOLD
from market_watcher.ui.styles import header_html, risk_badge


SUPPLIER_LABELS = {
    "microsoft": "Microsoft Azure",
    "aws": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
}

SUPPLIER_LOGOS = {
    "microsoft": "🔷",
    "aws": "🟠",
    "gcp": "🔴",
}

TIER_COLORS = {
    "Preferred": "#0F2067",
    "Approved": "#9B2BF7",
}


def render():
    st.markdown(header_html(
        "Buyer Guide — Self-Serve Buying",
        f"Cloud Infrastructure · Purchases under £{SPEND_THRESHOLD:,} · Powered by PSL catalogue"
    ), unsafe_allow_html=True)

    # Criteria weights sidebar
    with st.sidebar:
        st.markdown("### Ranking Criteria")
        st.markdown("*Adjust weights to re-rank suppliers in real time*")

        weights = {
            "price": st.slider("💰 Price / Value", 0.0, 1.0, 0.25, 0.05, key="w_price"),
            "quality": st.slider("⭐ Quality / Reliability", 0.0, 1.0, 0.30, 0.05, key="w_quality"),
            "esg": st.slider("🌱 ESG / Sustainability", 0.0, 1.0, 0.15, 0.05, key="w_esg"),
            "delivery_speed": st.slider("⚡ Delivery Speed", 0.0, 1.0, 0.15, 0.05, key="w_delivery"),
            "payment_terms": st.slider("📅 Payment Terms", 0.0, 1.0, 0.05, 0.05, key="w_payment"),
            "support": st.slider("🤝 Support / SLA", 0.0, 1.0, 0.10, 0.05, key="w_support"),
        }

        total = sum(weights.values())
        if total > 0:
            st.caption(f"Total weight: {total:.2f} (will be normalised to 1.0)")
        else:
            st.warning("Set at least one weight above 0.")

    # Live ranking panel
    col_rank, col_chat = st.columns([1, 1])

    with col_rank:
        st.subheader("Live Supplier Ranking")
        _render_live_ranking(weights)

    with col_chat:
        st.subheader("Ask the Buyer Guide")
        _render_chat()


def _render_live_ranking(weights: dict):
    """Render the PSL ranking — re-runs every time sliders change."""
    try:
        from market_watcher.tools.mock_services import get_psl_search

        ranked = get_psl_search(category="Cloud Infrastructure", criteria_weights=weights)

        for supplier in ranked:
            rank = supplier["rank"]
            name = supplier["name"]
            score = supplier.get("weighted_score", 0)
            tier = supplier.get("tier", "")
            tier_color = TIER_COLORS.get(tier, "#B999F6")
            logo = SUPPLIER_LOGOS.get(supplier["supplier_id"], "🔹")
            scores = supplier.get("scores", {})

            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")

            with st.container():
                st.markdown(
                    f"""<div style="border:1px solid #DECFFF;border-radius:8px;padding:12px;
                                    margin-bottom:8px;background:#fafafa;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-size:1.1rem;font-weight:bold;color:#0F2067;">
                                {medal} {logo} {name}
                            </span>
                            <span style="background:{tier_color};color:white;padding:2px 8px;
                                         border-radius:4px;font-size:0.75rem;font-weight:bold;">
                                {tier}
                            </span>
                        </div>
                        <div style="margin-top:6px;">
                            <span style="font-size:1.4rem;font-weight:bold;color:#9B2BF7;">
                                {score:.2f}
                            </span>
                            <span style="font-size:0.75rem;color:#888;"> weighted score</span>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                # Score breakdown
                with st.expander("Score breakdown", expanded=False):
                    for k, v in scores.items():
                        label_map = {
                            "price": "💰 Price",
                            "quality": "⭐ Quality",
                            "esg": "🌱 ESG",
                            "delivery_speed": "⚡ Speed",
                            "payment_terms": "📅 Payment",
                            "support": "🤝 Support",
                        }
                        bar_color = "#85DB9C" if v >= 0.8 else ("#B999F6" if v >= 0.6 else "#DECFFF")
                        st.markdown(
                            f'{label_map.get(k, k)}: <span style="color:#0F2067;font-weight:bold;">{v:.2f}</span>',
                            unsafe_allow_html=True,
                        )
                        st.progress(v)

                if supplier.get("contact"):
                    st.caption(f"Contact: {supplier['contact']}")

    except Exception as e:
        st.error(f"Ranking error: {e}")
        st.info("Ensure mock_psl_search tool is available.")


def _render_chat():
    """Conversational Buyer Guide interface."""
    if "buyer_messages" not in st.session_state:
        st.session_state["buyer_messages"] = []
        st.session_state["buyer_history"] = []

    # Display existing messages
    for msg in st.session_state["buyer_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Suggested prompts
    if not st.session_state["buyer_messages"]:
        st.markdown("**Try asking:**")
        suggestions = [
            "I need 50 RHEL licences for Q3",
            "Find me a cloud storage supplier — ESG is our top priority",
            "Compare Microsoft and AWS on payment terms",
            "Which supplier has the best support SLA?",
        ]
        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            if cols[i % 2].button(s, key=f"suggest_{i}"):
                st.session_state["buyer_messages"].append({"role": "user", "content": s})
                _send_message(s)
                st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask about suppliers, pricing, certifications..."):
        st.session_state["buyer_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        _send_message(prompt)
        st.rerun()


def _send_message(message: str):
    with st.chat_message("assistant"):
        with st.spinner("Buyer Guide agent thinking..."):
            try:
                from market_watcher.subagents.query import run_buyer_query
                result = run_buyer_query(message, st.session_state.get("buyer_history", []))

                if result["status"] == "ok":
                    response = result["response"]
                    st.session_state["buyer_history"] = result["history"]
                else:
                    response = f"Sorry, I encountered an issue: {result.get('message', 'Unknown error')}"

            except Exception as e:
                response = f"Agent error: {e}"

            st.markdown(response)
            st.session_state["buyer_messages"].append({"role": "assistant", "content": response})
