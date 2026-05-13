"""Placeholder view for categories that have not been fully onboarded onto Category Watcher yet.

Renders a credible 'category card' with metadata + 'Activate this category' CTA.
The IT Software category uses the full Digest/Dashboard/Strategy stack instead.
"""

import time
import streamlit as st

from market_watcher.ui.styles import header_html


STATUS_COLORS = {
    "Live": "#85DB9C", "Pilot": "#B999F6", "Coming Soon": "#DECFFF",
}


def render(category: dict):
    st.markdown(header_html(
        f"{category['icon']}  {category['name']}",
        f"Owner: {category['owner']} · Last reviewed {category['last_review']} · {category['vendor_count']} vendors · £{category['spend_gbp_m']:.1f}m annual spend"
    ), unsafe_allow_html=True)

    status = category["status"]
    bg = STATUS_COLORS.get(status, "#DECFFF")

    # Status banner
    st.markdown(
        f"""<div style="background:{bg};border-left:6px solid #0F2067;padding:12px 18px;border-radius:6px;margin-bottom:14px;">
            <span style="font-size:0.75rem;color:#0F2067;font-weight:bold;letter-spacing:1px;">CATEGORY STATUS</span>
            <span style="float:right;background:#0F2067;color:white;padding:2px 12px;border-radius:4px;font-weight:bold;">{status.upper()}</span>
            <div style="font-size:0.95rem;color:#0F2067;margin-top:6px;">{category['description']}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    # KPI strip
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annual spend", f"£{category['spend_gbp_m']:.0f}m")
    c2.metric("Vendors in scope", category["vendor_count"])
    c3.metric("Category owner", category["owner"])
    c4.metric("Next review", category["next_review"])

    st.markdown("---")

    # Top vendors + frameworks
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### 🏢 Top vendors")
        for v in category["top_vendors"]:
            st.markdown(
                f"""<div style="background:#fafafa;border-left:4px solid #9B2BF7;padding:6px 12px;border-radius:4px;margin-bottom:4px;color:#0F2067;font-weight:bold;">
                    {v}
                </div>""",
                unsafe_allow_html=True,
            )

    with col_r:
        st.markdown("#### 🧰 Frameworks already applied")
        for f in category["frameworks_applied"]:
            st.markdown(
                f"""<div style="background:#fafafa;border-left:4px solid #85DB9C;padding:6px 12px;border-radius:4px;margin-bottom:4px;color:#0F2067;">
                    ✓ {f}
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # What activating Category Watcher would unlock
    st.markdown("#### 🚀 What activating Category Watcher would unlock for this category")
    rows = [
        ("📋 Monday Morning Intelligence Digest", "Weekly agent-curated briefing — risks, renewals, certs, market signals."),
        ("📊 Live Category Manager Dashboard", f"PESTLE, risk register, regulations, spend cube, contract pipeline, vendor 360 for all {category['vendor_count']} vendors."),
        ("📘 Consolidated Category Strategy", "Porter's 5 Forces · SWOT (buyer-view) · Kraljic Matrix · sourcing strategy · stakeholder map."),
        ("🛰️ Distribution to downstream agents", "Auto-route findings to Ariba, Pactum, RFx Agent, Contracting Agent, TPRM, Power BI, Outlook, MS Teams."),
        ("🔍 Data-source integrations", "D&B · Bloomberg · Achilles · Companies House · Gartner · Forrester · Ariba · Ecovadis."),
    ]
    for title, body in rows:
        st.markdown(
            f"""<div style="background:#fafafa;border-left:4px solid #0F2067;padding:10px 14px;border-radius:4px;margin-bottom:6px;">
                <div style="font-weight:bold;color:#0F2067;">{title}</div>
                <div style="font-size:0.85rem;color:#444;margin-top:2px;">{body}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # CTA
    disabled = status == "Coming Soon"
    cta_label = {
        "Live": "✅ Category Watcher is live for this category",
        "Pilot": "🚀 Activate Category Watcher for this category",
        "Coming Soon": "⏳ Coming soon — backlog item",
    }.get(status, "Activate Category Watcher")

    if st.button(cta_label, use_container_width=True, type="primary",
                  disabled=(disabled or status == "Live"),
                  key=f"activate_{category['id']}"):
        _simulate_activation(category)


def _simulate_activation(category: dict):
    """Pretend to onboard a new category — terminal-style progress."""
    log_slot = st.empty()
    lines = []
    steps = [
        f"🔧 Provisioning Category Watcher workspace for **{category['name']}**...",
        "📡 Connecting Gemini agent to category data sources...",
        f"💼 Pulling D&B Risk Scores for {category['vendor_count']} vendors...",
        f"🇬🇧 Cross-referencing Companies House registry for UK-incorporated vendors...",
        "📊 Bootstrapping SAP Ariba spend-cube view for category...",
        "🧠 Generating Porter's 5 Forces and Kraljic Matrix with Gemini 2.5...",
        "🛰️ Registering downstream agent routes (Ariba · Pactum · RFx · TPRM)...",
        "✅ Category onboarded. Awaiting Category Manager sign-off."
    ]
    progress = st.progress(0, text="Starting...")
    for i, step in enumerate(steps):
        lines.append(step)
        log_slot.markdown(
            f"""<div style="background:#0F2067;color:#85DB9C;padding:10px 14px;border-radius:8px;
                          font-family:monospace;font-size:0.85rem;line-height:1.7;">
                {'<br>'.join(lines)}
            </div>""",
            unsafe_allow_html=True,
        )
        progress.progress((i + 1) / len(steps), text=step.replace("**", ""))
        time.sleep(0.45)
    progress.empty()
    st.success(f"✨ Category Watcher activated for {category['name']} — Category Manager has been notified.")
