"""Tab 1 — Monday Morning Digest: agent theatre → in-UI findings visuals → distribute to downstream agents."""

import random
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from market_watcher.config import DEMO_CATEGORY
from market_watcher.ui.styles import header_html, risk_badge
from market_watcher.ui.agent_theatre import stream_with_progress
from market_watcher.tools.mock_services import (
    get_industry_risks, get_certification_register, get_contract_pipeline,
    get_market_intel, get_downstream_agents, list_suppliers,
)


SEV_COLORS = {"High": "#9B2BF7", "Medium": "#B999F6", "Low": "#85DB9C"}


def render():
    st.markdown(header_html(
        "Monday Morning Intelligence Scan",
        f"Market Watcher · {DEMO_CATEGORY} · {datetime.now().strftime('%A %d %B %Y')}"
    ), unsafe_allow_html=True)

    st.markdown(
        "The Market Watcher agent pulls vendor 360 profiles, Gartner/Forrester signals, "
        "Ariba spend, the certification register, regulatory landscape, and PESTLE intelligence — "
        "then synthesises a category-manager briefing. Findings can be routed to downstream agents (Ariba, Pactum, RFx, Contracting, TPRM)."
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("▶  Run Monday Scan now", key="run_scan", use_container_width=True, type="primary"):
            _run_scan()
    with col2:
        if st.session_state.get("scan_complete"):
            st.success("Last scan: now")

    if st.session_state.get("scan_complete"):
        _render_findings()
        st.markdown("---")
        _render_distribute_panel()


def _run_scan():
    stream_with_progress(track="scan", message_delay=0.35)

    try:
        from market_watcher.subagents.batch import run_monday_scan
        with st.spinner("Synthesising findings with Gemini..."):
            result = run_monday_scan(DEMO_CATEGORY)
        st.session_state["digest_result"] = result
        st.session_state["scan_complete"] = True
        if result.get("status") == "ok":
            st.success("✅ Scan complete.")
        else:
            st.error(f"Agent error: {result.get('message', 'unknown')}")
    except Exception as e:
        st.session_state["digest_result"] = {"status": "error", "message": str(e)}
        st.error(f"Agent error: {e}")


def _render_findings():
    result = st.session_state.get("digest_result", {})
    if result.get("status") == "error":
        st.error(f"Last scan failed: {result.get('message', '')}")
        return

    st.markdown("---")
    st.subheader("📈 This Week's Findings")

    # Sources-scanned badge row — visible proof of what the agent touched
    _render_sources_badges()

    # KPI strip
    risks = get_industry_risks()
    certs = get_certification_register()
    pipeline = get_contract_pipeline()
    high_risks = [r for r in risks if r["severity"] == "High"]
    expired = [c for c in certs if c["status"] == "Expired"]
    expiring = [c for c in certs if c["status"] == "Expiring Soon"]
    urgent_renewals = [c for c in pipeline if c["priority"] in ("Critical", "High")]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔴 High Risks", len(high_risks))
    c2.metric("❌ Certs Expired", len(expired))
    c3.metric("⚠️ Certs Expiring", len(expiring))
    c4.metric("📋 Urgent Renewals", len(urgent_renewals))
    c5.metric("📰 Sources Cited", len(result.get("news_sources", [])))

    # Agent summary block
    if result.get("summary"):
        st.markdown(
            f"""<div style="background:#DECFFF;border-left:6px solid #0F2067;padding:14px 18px;border-radius:6px;margin:14px 0;">
                <div style="font-size:0.75rem;color:#0F2067;font-weight:bold;letter-spacing:1px;">🧠 GEMINI AGENT SUMMARY</div>
                <div style="font-size:1.0rem;color:#0F2067;margin-top:6px;line-height:1.5;">{result['summary']}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # Two-column body
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 🚨 Top Risks This Week")
        for r in high_risks[:5]:
            bg = SEV_COLORS[r["severity"]]
            st.markdown(
                f"""<div style="border-left:4px solid {bg};padding:8px 12px;background:#fafafa;border-radius:4px;margin-bottom:8px;">
                    <div style="font-weight:bold;color:#0F2067;font-size:0.92rem;">{r['title']}</div>
                    <div style="font-size:0.85rem;color:#444;margin-top:4px;">{r['description']}</div>
                    <div style="font-size:0.75rem;color:#777;margin-top:4px;">Owner: {r['owner']} · {r['open_actions']} open actions</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("#### 📋 Renewal Pipeline (Next 90 Days)")
        urgent = sorted(urgent_renewals, key=lambda x: x["expiry"])[:4]
        for c in urgent:
            prio_color = {"Critical": "#9B2BF7", "High": "#B999F6"}.get(c["priority"], "#85DB9C")
            st.markdown(
                f"""<div style="background:#fafafa;padding:8px 12px;border-radius:4px;margin-bottom:6px;border:1px solid #DECFFF;">
                    <span style="background:{prio_color};color:white;padding:2px 6px;border-radius:3px;font-size:0.7rem;font-weight:bold;">{c['priority']}</span>
                    <strong style="color:#0F2067;margin-left:6px;">{c['supplier']}</strong>
                    <span style="color:#666;font-size:0.85rem;"> — expires {c['expiry']} (£{c['value_gbp']:,})</span>
                    <div style="font-size:0.75rem;color:#888;margin-top:2px;">{c['status']} · Owner: {c['owner']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    with col_right:
        st.markdown("#### ⚠️ Certification Alerts")
        cert_attention = expired + expiring
        for c in sorted(cert_attention, key=lambda x: x["days_to_expiry"])[:5]:
            icon = "❌" if c["status"] == "Expired" else "⚠️"
            color = "#9B2BF7" if c["status"] == "Expired" else "#B999F6"
            days_text = f"{abs(c['days_to_expiry'])} days {'overdue' if c['days_to_expiry'] < 0 else 'until expiry'}"
            st.markdown(
                f"""<div style="border-left:4px solid {color};padding:8px 12px;background:#fafafa;border-radius:4px;margin-bottom:8px;">
                    <div style="font-weight:bold;color:#0F2067;font-size:0.9rem;">{icon} {c['supplier_name']} — {c['type']}</div>
                    <div style="font-size:0.8rem;color:#444;margin-top:2px;">Expires {c['expiry']} · {days_text}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("#### 📰 Top Market Signals")
        intel = get_market_intel(limit=4)
        for item in intel:
            tag_colors = {"analyst": "#0F2067", "news": "#9B2BF7", "regulation": "#B999F6", "internal": "#85DB9C"}
            bg = tag_colors.get(item.get("tag", "news"), "#DECFFF")
            st.markdown(
                f"""<div style="border-left:4px solid {bg};padding:8px 12px;background:#fafafa;border-radius:4px;margin-bottom:8px;">
                    <div style="font-weight:bold;color:#0F2067;font-size:0.88rem;">{item['title']}</div>
                    <div style="font-size:0.8rem;color:#444;margin-top:3px;">{item['snippet'][:160]}...</div>
                    <div style="font-size:0.72rem;color:#888;margin-top:4px;">
                        {item['source']} · {item['date']} ·
                        <span style="background:{bg};color:white;padding:1px 5px;border-radius:3px;font-size:0.7rem;">{item.get('tag', 'news').upper()}</span>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    # Recommended next actions
    actions = result.get("top_actions", [])
    if actions:
        st.markdown("#### ✅ Recommended Next Actions")
        for i, a in enumerate(actions, 1):
            st.markdown(
                f"""<div style="background:#85DB9C;color:#0F2067;padding:8px 14px;border-radius:6px;margin-bottom:6px;font-size:0.9rem;">
                    <strong>{i}.</strong> {a}
                </div>""",
                unsafe_allow_html=True,
            )

    if result.get("news_sources"):
        st.caption(f"Sources cited by agent: {' · '.join(result['news_sources'][:8])}")


def _render_sources_badges():
    """Show the data sources the agent pulled from this run."""
    sources = [
        ("💼", "Dun & Bradstreet", "Risk scores · PayDex · family tree", "#0F2067"),
        ("📈", "Bloomberg Intelligence", "Market cap · M&A · earnings", "#9B2BF7"),
        ("🏷️", "Achilles", "UVDB · JOSCAR · audit evidence", "#B999F6"),
        ("🇬🇧", "Companies House", "UK filings · PSC · charges", "#0F2067"),
        ("📡", "Gartner", "Magic Quadrant · Hype Cycle", "#9B2BF7"),
        ("📡", "Forrester", "Wave reports", "#B999F6"),
        ("📊", "SAP Ariba", "Spend cube · contracts", "#85DB9C"),
        ("🧾", "Ecovadis", "ESG scorecards", "#85DB9C"),
        ("🌐", "FT · Reuters · Bloomberg News", "Real-time news", "#0F2067"),
    ]
    st.markdown(
        "<div style='font-size:0.78rem;color:#666;margin-bottom:6px;'>"
        "🛰️ <b>Data sources scanned by the agent this run:</b>"
        "</div>",
        unsafe_allow_html=True,
    )
    badges_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;'>"
    for icon, name, scope, color in sources:
        badges_html += (
            f"<div style='border:1px solid {color};border-left:4px solid {color};"
            f"background:#fafafa;padding:6px 10px;border-radius:6px;font-size:0.78rem;"
            f"min-width:160px;'>"
            f"<div style='color:#0F2067;font-weight:bold;'>{icon} {name}</div>"
            f"<div style='color:#666;font-size:0.7rem;margin-top:2px;'>{scope}</div>"
            f"</div>"
        )
    badges_html += "</div>"
    st.markdown(badges_html, unsafe_allow_html=True)


# ── Distribute panel ────────────────────────────────────────────────────────

def _render_distribute_panel():
    st.subheader("🛰️ Distribute Findings to Downstream Agents & Systems")
    st.caption("Select which agents and systems of record should receive this scan's findings. Each system gets a tailored subset.")

    agents = get_downstream_agents()

    # Initialise selection state
    if "selected_agents" not in st.session_state:
        # Default: pre-select the Live ones except OFGEM (Coming Soon)
        st.session_state["selected_agents"] = {a["id"]: (a["status"] == "Live") for a in agents}

    cols = st.columns(2)
    for i, a in enumerate(agents):
        with cols[i % 2]:
            status_color = {"Live": "#85DB9C", "Beta": "#B999F6", "Coming Soon": "#DECFFF"}.get(a["status"], "#DECFFF")
            disabled = a["status"] == "Coming Soon"

            checked = st.checkbox(
                f"{a['icon']}  **{a['name']}**",
                value=st.session_state["selected_agents"].get(a["id"], False) and not disabled,
                key=f"agent_chk_{a['id']}",
                disabled=disabled,
            )
            st.session_state["selected_agents"][a["id"]] = checked

            st.markdown(
                f"""<div style="margin:-12px 0 14px 28px;padding:8px 12px;border-left:3px solid {a['color']};background:#fafafa;border-radius:4px;">
                    <span style="background:{status_color};color:#0F2067;padding:1px 7px;border-radius:3px;font-size:0.7rem;font-weight:bold;">{a['status']}</span>
                    <span style="font-size:0.72rem;color:#666;margin-left:6px;">{a['type']}</span>
                    <div style="font-size:0.82rem;color:#333;margin-top:6px;"><b>Receives:</b> {a['receives']}</div>
                    <div style="font-size:0.78rem;color:#555;margin-top:3px;"><b>Scope:</b> {a['scope']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # Distribute action
    st.markdown("---")
    selected = [a for a in agents if st.session_state["selected_agents"].get(a["id"])]
    col_btn, col_count = st.columns([2, 1])
    with col_btn:
        if st.button(f"📡  Distribute findings to {len(selected)} system{'s' if len(selected) != 1 else ''}",
                      use_container_width=True, type="primary",
                      disabled=len(selected) == 0):
            _distribute(selected)
    with col_count:
        st.metric("Selected", f"{len(selected)} / {len([a for a in agents if a['status'] != 'Coming Soon'])}")


def _distribute(selected: list[dict]):
    """Simulated distribution to downstream systems. Fakes API calls with progress + toasts."""
    progress = st.progress(0, text="Preparing payloads...")
    log_slot = st.empty()
    lines = []

    for i, a in enumerate(selected):
        lines.append(f"📡  Sending to **{a['name']}** ({a['type']})...")
        log_slot.markdown(
            f"""<div style="background:#0F2067;color:#85DB9C;padding:10px 14px;border-radius:8px;
                          font-family:monospace;font-size:0.85rem;line-height:1.7;">
                {'<br>'.join(lines)}
            </div>""",
            unsafe_allow_html=True,
        )
        progress.progress((i + 0.5) / len(selected), text=f"Routing to {a['name']}...")
        time.sleep(0.4 + random.uniform(0, 0.3))

        lines[-1] = f"✅  **{a['name']}** — payload delivered, ack received."
        log_slot.markdown(
            f"""<div style="background:#0F2067;color:#85DB9C;padding:10px 14px;border-radius:8px;
                          font-family:monospace;font-size:0.85rem;line-height:1.7;">
                {'<br>'.join(lines)}
            </div>""",
            unsafe_allow_html=True,
        )
        progress.progress((i + 1) / len(selected), text=f"Delivered to {a['name']}")
        time.sleep(0.2)

    progress.empty()
    st.success(f"🚀  Findings successfully distributed to {len(selected)} downstream agent{'s' if len(selected) != 1 else ''}.")
    st.balloons()
