"""Tab 4 — Consolidated Category Strategy view.

Holds Porter's 5 Forces, PESTLE, SWOT, Kraljic Matrix, sourcing strategy,
objectives and stakeholders for the IT Software category from Centrica's
buyer perspective.
"""

import streamlit as st

from market_watcher.config import DEMO_CATEGORY
from market_watcher.ui.styles import header_html
from market_watcher.tools.mock_services import get_category_strategy, get_pestle


LEVEL_COLORS = {"High": "#9B2BF7", "Medium": "#B999F6", "Low": "#85DB9C"}
STATUS_COLORS = {"On track": "#85DB9C", "At risk": "#B999F6", "Behind": "#9B2BF7"}


def render():
    strat = get_category_strategy()
    pestle = get_pestle()

    st.markdown(header_html(
        f"Category Strategy — {strat['category']}",
        f"Owner: {strat['owner']} · Last reviewed {strat['last_reviewed']} · Horizon {strat['strategy_horizon']}"
    ), unsafe_allow_html=True)

    # Vision block
    st.markdown(
        f"""<div style="background:#DECFFF;border-left:6px solid #0F2067;padding:14px 18px;border-radius:6px;margin-bottom:14px;">
            <div style="font-size:0.75rem;color:#0F2067;font-weight:bold;letter-spacing:1px;">📘 CATEGORY VISION</div>
            <div style="font-size:1.0rem;color:#0F2067;margin-top:6px;line-height:1.5;">{strat['vision']}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    sections = [
        "🎯 Objectives",
        "🏟️ Porter's 5 Forces",
        "🌍 PESTLE",
        "🧭 SWOT (Buyer view)",
        "📐 Kraljic Matrix",
        "🛒 Sourcing Strategy",
        "👥 Stakeholder Map",
        "🧰 Frameworks Index",
    ]
    section = st.radio("View", sections, horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    if section.startswith("🎯"):
        _render_objectives(strat)
    elif section.startswith("🏟️"):
        _render_porters(strat)
    elif section.startswith("🌍"):
        _render_pestle(pestle)
    elif section.startswith("🧭"):
        _render_swot(strat)
    elif section.startswith("📐"):
        _render_kraljic(strat)
    elif section.startswith("🛒"):
        _render_sourcing(strat)
    elif section.startswith("👥"):
        _render_stakeholders(strat)
    elif section.startswith("🧰"):
        _render_frameworks(strat)


# ── Section renderers ────────────────────────────────────────────────────────

def _render_objectives(strat: dict):
    st.subheader("🎯 Strategic Objectives")
    st.caption(f"Horizon: {strat['strategy_horizon']}  ·  Next review: {strat['next_review']}")
    for obj in strat["objectives"]:
        bg = STATUS_COLORS.get(obj["status"], "#DECFFF")
        st.markdown(
            f"""<div style="border:1px solid #DECFFF;border-left:5px solid {bg};
                          padding:10px 14px;background:#fafafa;border-radius:6px;margin-bottom:8px;">
                <div style="font-weight:bold;color:#0F2067;">{obj['objective']}</div>
                <div style="font-size:0.85rem;color:#444;margin-top:4px;">
                    🎯 Target: <b>{obj['target']}</b>
                    <span style="float:right;background:{bg};color:#0F2067;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:bold;">{obj['status']}</span>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_porters(strat: dict):
    porters = strat["porters"]
    st.subheader(f"🏟️ {porters['title']}")
    st.caption("Industry-level competitive analysis from Centrica's buyer perspective.")

    # Centre force (Industry rivalry) goes in the middle visually — we'll do a 2-column grid for now
    forces = porters["forces"]
    cols = st.columns(2)
    for i, f in enumerate(forces):
        with cols[i % 2]:
            bg = LEVEL_COLORS.get(f["level"], "#B999F6")
            trend = {"rising": "↗️ rising", "stable": "→ stable", "falling": "↘️ falling"}.get(f["trend"], "→")
            st.markdown(
                f"""<div style="border:1px solid #DECFFF;border-radius:8px;padding:14px;margin-bottom:14px;background:white;">
                    <div style="font-size:1.0rem;font-weight:bold;color:#0F2067;">
                        {f['force']}
                        <span style="float:right;background:{bg};color:white;padding:2px 8px;border-radius:4px;font-size:0.7rem;">{f['level']} {trend}</span>
                    </div>
                    <div style="margin-top:8px;font-size:0.9rem;color:#333;line-height:1.5;">{f['assessment']}</div>
                    <div style="margin-top:10px;background:#DECFFF;padding:8px 10px;border-radius:4px;font-size:0.85rem;color:#0F2067;">
                        <b>Implication for Centrica:</b> {f['implication']}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )


def _render_pestle(pestle: dict):
    """Reuse the existing PESTLE renderer (also lives in Dashboard tab) so strategy is self-contained."""
    st.subheader("🌍 PESTLE — Macro-Environmental Scan")
    st.caption(f"Last refreshed {pestle['last_updated']} from Centrica Strategy intranet + analyst syndication.")

    cols = st.columns(2)
    for i, f in enumerate(pestle["factors"]):
        with cols[i % 2]:
            trend_icon = {"rising": "↗️", "stable": "→", "falling": "↘️"}.get(f["trend"], "→")
            impact_bg = LEVEL_COLORS.get(f["impact"], "#B999F6")
            st.markdown(
                f"""<div style="border:1px solid #DECFFF;border-radius:8px;padding:14px;margin-bottom:14px;background:white;">
                    <div style="font-size:1.05rem;font-weight:bold;color:#0F2067;">
                        {f['icon']} {f['dimension']}
                        <span style="float:right;background:{impact_bg};color:white;padding:2px 8px;border-radius:4px;font-size:0.7rem;">
                            {f['impact']} {trend_icon}
                        </span>
                    </div>
                    <div style="font-weight:bold;color:#0F2067;margin-top:8px;">{f['headline']}</div>
                    <div style="margin-top:6px;font-size:0.88rem;color:#333;line-height:1.5;">{f['detail']}</div>
                    <div style="margin-top:8px;font-size:0.72rem;color:#888;font-style:italic;">
                        Sources: {' · '.join(f['sources'])}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )


def _render_swot(strat: dict):
    swot = strat["swot"]
    st.subheader("🧭 SWOT — Buyer (Centrica Procurement) View")
    st.caption("Internal strengths/weaknesses + external opportunities/threats from the procurement seat.")

    palette = {
        "strengths":    {"color": "#85DB9C", "label": "💪 STRENGTHS"},
        "weaknesses":   {"color": "#9B2BF7", "label": "⚠️ WEAKNESSES"},
        "opportunities":{"color": "#0F2067", "label": "🚀 OPPORTUNITIES"},
        "threats":      {"color": "#B999F6", "label": "🌪️ THREATS"},
    }

    col_l, col_r = st.columns(2)
    for col, keys in [(col_l, ["strengths", "weaknesses"]), (col_r, ["opportunities", "threats"])]:
        with col:
            for key in keys:
                p = palette[key]
                items_html = "".join(f"<li style='margin:4px 0;'>{x}</li>" for x in swot[key])
                st.markdown(
                    f"""<div style="border:2px solid {p['color']};border-radius:8px;padding:14px;margin-bottom:14px;background:white;">
                        <div style="background:{p['color']};color:white;padding:4px 10px;border-radius:4px;font-weight:bold;font-size:0.85rem;display:inline-block;letter-spacing:1px;">
                            {p['label']}
                        </div>
                        <ul style="margin-top:10px;margin-bottom:0;font-size:0.9rem;color:#333;line-height:1.5;padding-left:20px;">{items_html}</ul>
                    </div>""",
                    unsafe_allow_html=True,
                )


def _render_kraljic(strat: dict):
    k = strat["kraljic"]
    st.subheader(f"📐 {k['title']}")
    st.caption(k["description"])

    # 2x2 grid: Strategic (top-left, high impact/high risk per convention)
    # Layout: top row = high spend (Strategic, Leverage), bottom row = low spend (Bottleneck, Routine)
    # within row: left = high risk, right = low risk
    by_name = {q["name"]: q for q in k["quadrants"]}

    # Top row
    top_l, top_r = st.columns(2)
    with top_l:
        _kraljic_card(by_name["Strategic"])
    with top_r:
        _kraljic_card(by_name["Leverage"])
    bot_l, bot_r = st.columns(2)
    with bot_l:
        _kraljic_card(by_name["Bottleneck"])
    with bot_r:
        _kraljic_card(by_name["Routine"])

    st.markdown("")
    st.markdown(
        f"""<div style="display:flex;justify-content:space-between;font-size:0.78rem;color:#666;margin-top:6px;">
            <div>↑ {k['axes']['y']}</div>
            <div>{k['axes']['x']}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def _kraljic_card(q: dict):
    vendors_html = "".join(
        f"<span style='background:white;color:{q['color']};padding:2px 8px;border-radius:4px;margin:2px 4px 2px 0;border:1px solid {q['color']};display:inline-block;font-size:0.78rem;font-weight:bold;'>{v}</span>"
        for v in q["vendors"]
    )
    st.markdown(
        f"""<div style="border:2px solid {q['color']};border-radius:10px;padding:14px;background:white;min-height:180px;margin-bottom:14px;">
            <div style="background:{q['color']};color:white;padding:4px 10px;border-radius:4px;font-weight:bold;font-size:0.95rem;display:inline-block;">
                {q['name']}
            </div>
            <div style="font-size:0.75rem;color:#666;margin-top:4px;">{q['subtitle']}</div>
            <div style="margin-top:10px;font-size:0.82rem;color:#333;font-style:italic;">{q['approach']}</div>
            <div style="margin-top:12px;">{vendors_html}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def _render_sourcing(strat: dict):
    s = strat["sourcing_strategy"]
    st.subheader("🛒 Sourcing Strategy")
    st.markdown(
        f"<div style='font-size:0.95rem;color:#0F2067;margin-bottom:14px;'><b>Overall approach:</b> {s['approach']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("**Allocation targets per sub-category:**")

    import pandas as pd
    rows = []
    for a in s["allocation_targets"]:
        rows.append({
            "Sub-category": a["segment"],
            "Current": a["current"],
            "Target (FY28)": a["target"],
            "Rationale": a["rationale"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_stakeholders(strat: dict):
    st.subheader("👥 Stakeholder Map")
    st.caption("Cross-functional stakeholders for the IT Software category.")

    for s in strat["stakeholders"]:
        st.markdown(
            f"""<div style="border-left:4px solid #0F2067;padding:8px 14px;background:#fafafa;border-radius:4px;margin-bottom:8px;">
                <div style="font-weight:bold;color:#0F2067;">{s['role']}</div>
                <div style="font-size:0.85rem;color:#444;">{s['name']}</div>
                <div style="font-size:0.78rem;color:#666;margin-top:2px;font-style:italic;">{s['interest']}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_frameworks(strat: dict):
    st.subheader("🧰 Frameworks Applied")
    st.caption("Frameworks used in maintaining this category strategy.")

    for f in strat["frameworks_applied"]:
        st.markdown(
            f"""<div style="border:1px solid #DECFFF;padding:10px 14px;border-radius:6px;background:white;margin-bottom:6px;">
                <span style="font-weight:bold;color:#0F2067;">{f['name']}</span>
                <span style="color:#666;font-size:0.85rem;"> — {f['purpose']}</span>
                <span style="float:right;color:#9B2BF7;font-size:0.78rem;">Owner: {f['owner']}</span>
            </div>""",
            unsafe_allow_html=True,
        )
