"""Tab 2 — Full Category Manager Dashboard for IT Software."""

import json
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from market_watcher.config import DEMO_CATEGORY, FIXTURES_DIR
from market_watcher.ui.styles import header_html, risk_badge
from market_watcher.ui.agent_theatre import stream
from market_watcher.tools.mock_services import (
    get_supplier_360, list_suppliers, get_certification_register,
    get_pestle, get_industry_risks, get_regulations,
    get_contract_pipeline, get_market_intel,
)
from market_watcher.tools.document_gen import _draft_cert_chase_email


PESTLE_COLORS = {
    "Political": "#0F2067", "Economic": "#9B2BF7", "Social": "#B999F6",
    "Technological": "#85DB9C", "Legal": "#0F2067", "Environmental": "#85DB9C",
}

SEV_BG = {"High": "#9B2BF7", "Medium": "#B999F6", "Low": "#85DB9C", "Critical": "#0F2067"}


def render():
    st.markdown(header_html(
        "Category Manager Dashboard",
        f"{DEMO_CATEGORY} · 8 PSL vendors · Live agent-curated view"
    ), unsafe_allow_html=True)

    # Top-bar refresh button → triggers agent theatre
    if st.button("🔄  Refresh from sources (Ariba · Gartner · D&B · Ecovadis)", use_container_width=True):
        with st.container():
            stream(track="dashboard", message_delay=0.25)
        st.success("✅ All sources refreshed — data below is current.")

    # ── Top-line metrics ─────────────────────────────────────────────────────
    suppliers = list_suppliers()
    total_spend = sum(s["spend_ytd_gbp"] for s in suppliers)
    total_high_risks = sum(s["high_risks"] for s in suppliers)
    certs = get_certification_register()
    expired = sum(1 for c in certs if c["status"] == "Expired")
    expiring = sum(1 for c in certs if c["status"] == "Expiring Soon")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active PSL vendors", len(suppliers))
    c2.metric("YTD spend", f"£{total_spend/1_000_000:.2f}m")
    c3.metric("High-priority risks", total_high_risks)
    c4.metric("Certs expiring <90d", expiring)
    c5.metric("Certs expired", expired, delta_color="inverse")

    # ── Section nav ──────────────────────────────────────────────────────────
    sections = [
        "🏢 Vendor Landscape",
        "📊 Spend Analysis",
        "🌍 PESTLE",
        "⚠️ Risk Register",
        "⚖️ Regulations",
        "📋 Contract Pipeline",
        "🔐 Certifications",
        "📰 Market Intelligence",
        "🔍 Vendor 360",
    ]
    section = st.radio("View", sections, horizontal=True, label_visibility="collapsed")

    st.markdown("---")
    if section.startswith("🏢"):
        _render_vendor_landscape(suppliers)
    elif section.startswith("📊"):
        _render_spend_analysis()
    elif section.startswith("🌍"):
        _render_pestle()
    elif section.startswith("⚠️"):
        _render_risk_register()
    elif section.startswith("⚖️"):
        _render_regulations()
    elif section.startswith("📋"):
        _render_pipeline()
    elif section.startswith("🔐"):
        _render_certifications(certs)
    elif section.startswith("📰"):
        _render_market_intel()
    elif section.startswith("🔍"):
        _render_vendor_360()


# ── Section renderers ────────────────────────────────────────────────────────

def _render_vendor_landscape(suppliers: list[dict]):
    st.subheader("🏢 Vendor Landscape")
    st.caption("Pulled from Ariba supplier master + Gartner quadrant + D&B risk scores.")

    for s in suppliers:
        tier_color = {"Strategic": "#0F2067", "Preferred": "#9B2BF7", "Approved": "#B999F6"}.get(s["tier"], "#DECFFF")
        risk_chip = ""
        if s["high_risks"] > 0:
            risk_chip = f"<span style='background:#9B2BF7;color:white;padding:2px 8px;border-radius:4px;font-size:0.75rem;margin-left:8px;'>{s['high_risks']} HIGH RISK</span>"

        col_main, col_metrics = st.columns([2, 3])
        with col_main:
            st.markdown(
                f"""<div style="border-left:4px solid {tier_color};padding:8px 12px;background:#fafafa;border-radius:4px;">
                    <div style="font-size:1.05rem;font-weight:bold;color:#0F2067;">{s['name']}</div>
                    <div style="font-size:0.85rem;color:#666;">{s['subcategory']}</div>
                    <div style="margin-top:6px;">
                        <span style="background:{tier_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.75rem;">{s['tier']}</span>
                        <span style="color:#888;font-size:0.75rem;margin-left:8px;">{s['status']}</span>
                        {risk_chip}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
        with col_metrics:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("YTD Spend", f"£{s['spend_ytd_gbp']/1000:.0f}k")
            m2.metric("Gartner", s.get("gartner") or "—")
            m3.metric("D&B Risk", f"{s.get('dnb_score', '?')} / 5")
            m4.metric("Ecovadis", f"{s.get('ecovadis', '?')}/100")


def _render_spend_analysis():
    st.subheader("📊 Spend Analysis (last 5 months)")
    st.caption("Source: SAP Ariba Spend Cube · refreshed daily")

    df = pd.read_csv(FIXTURES_DIR / "spend_by_subcategory.csv")

    # By supplier
    by_supplier = df.groupby("supplier_name")["spend_gbp"].sum().reset_index().sort_values("spend_gbp", ascending=False)
    by_supplier.columns = ["Supplier", "Total Spend (£)"]

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Total spend by supplier**")
        st.bar_chart(by_supplier.set_index("Supplier"), color="#0F2067")
    with col_r:
        st.markdown("**Spend by sub-category**")
        by_subcat = df.groupby("subcategory")["spend_gbp"].sum().reset_index().sort_values("spend_gbp", ascending=False)
        st.bar_chart(by_subcat.set_index("subcategory"), color="#9B2BF7")

    st.markdown("**Monthly trend by supplier**")
    pivot = df.pivot_table(index="month", columns="supplier_name", values="spend_gbp", aggfunc="sum")
    st.line_chart(pivot)


def _render_pestle():
    pestle = get_pestle()
    st.subheader("🌍 PESTLE Analysis")
    st.caption(f"Last updated {pestle['last_updated']} · Source: Centrica Strategy intranet + analyst syndication")

    factors = pestle["factors"]
    cols = st.columns(2)
    for i, f in enumerate(factors):
        with cols[i % 2]:
            trend_icon = {"rising": "↗️", "stable": "→", "falling": "↘️"}.get(f["trend"], "→")
            impact_bg = SEV_BG.get(f["impact"], "#B999F6")
            st.markdown(
                f"""<div style="border:1px solid #DECFFF;border-radius:8px;padding:14px;margin-bottom:14px;background:white;">
                    <div style="font-size:1.1rem;font-weight:bold;color:#0F2067;">
                        {f['icon']} {f['dimension']}
                        <span style="float:right;background:{impact_bg};color:white;padding:2px 8px;border-radius:4px;font-size:0.7rem;">
                            {f['impact']} {trend_icon}
                        </span>
                    </div>
                    <div style="font-weight:bold;color:#0F2067;margin-top:8px;">{f['headline']}</div>
                    <div style="margin-top:6px;font-size:0.9rem;color:#333;">{f['detail']}</div>
                    <div style="margin-top:8px;font-size:0.75rem;color:#888;font-style:italic;">
                        Sources: {' · '.join(f['sources'])}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )


def _render_risk_register():
    risks = get_industry_risks()
    st.subheader("⚠️ Industry Risk Register")
    st.caption("Curated by Market Watcher agent · refreshed Monday 06:00 UTC")

    sev_counts = {"High": 0, "Medium": 0, "Low": 0}
    for r in risks:
        sev_counts[r["severity"]] = sev_counts.get(r["severity"], 0) + 1

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 High", sev_counts.get("High", 0))
    c2.metric("🟣 Medium", sev_counts.get("Medium", 0))
    c3.metric("🟢 Low", sev_counts.get("Low", 0))

    st.markdown("---")
    for r in risks:
        sev = r["severity"]
        bg = SEV_BG.get(sev, "#B999F6")
        trend_icon = {"rising": "↗️ rising", "stable": "→ stable", "falling": "↘️ improving"}.get(r["trend"], "→")
        st.markdown(
            f"""<div style="border-left:4px solid {bg};padding:10px 14px;background:#fafafa;border-radius:4px;margin-bottom:10px;">
                <div style="font-size:1.0rem;font-weight:bold;color:#0F2067;">
                    {r['id']} · {r['title']}
                    <span style="float:right;background:{bg};color:white;padding:2px 8px;border-radius:4px;font-size:0.75rem;">{sev}</span>
                </div>
                <div style="margin-top:6px;font-size:0.9rem;color:#333;">{r['description']}</div>
                <div style="margin-top:8px;font-size:0.85rem;color:#555;">
                    <b>Mitigant:</b> {r['mitigant']}
                </div>
                <div style="margin-top:6px;font-size:0.75rem;color:#888;">
                    Owner: {r['owner']} · Open actions: {r['open_actions']} · Trend: {trend_icon} · Likelihood: {r['likelihood']}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_regulations():
    regs = get_regulations()
    st.subheader("⚖️ Regulatory Landscape")
    st.caption("Sourced from DSIT, OFGEM, NCSC, EU Commission · agent-monitored")

    for r in regs:
        applic = r["applicability"] if isinstance(r["applicability"], list) else [r["applicability"]]
        applic_str = ", ".join(applic) if applic != ["all PSL vendors"] else "all PSL vendors"
        st.markdown(
            f"""<div style="border:1px solid #DECFFF;border-radius:8px;padding:14px;margin-bottom:12px;background:white;">
                <div style="font-size:1.05rem;font-weight:bold;color:#0F2067;">{r['regulation']}</div>
                <div style="font-size:0.8rem;color:#666;margin-top:2px;">{r['jurisdiction']}</div>
                <div style="margin-top:8px;font-size:0.9rem;">
                    <b>Status:</b> {r['status']}
                </div>
                <div style="margin-top:6px;font-size:0.9rem;color:#333;">{r['centrica_impact']}</div>
                <div style="margin-top:8px;font-size:0.75rem;color:#888;">
                    🎯 Applies to: {applic_str}  ·  📅 Deadline: {r['deadline']}  ·  👤 Owner: {r['owner']}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_pipeline():
    pipeline = get_contract_pipeline()
    st.subheader("📋 Contract Renewal Pipeline")
    st.caption("Source: Ariba contract registry · sorted by expiry date")

    rows = []
    for c in pipeline:
        prio_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(c["priority"], "")
        rows.append({
            "Priority": f"{prio_emoji} {c['priority']}",
            "Supplier": c["supplier"],
            "Contract Ref": c["ref"],
            "Expiry": c["expiry"],
            "Value (£)": f"£{c['value_gbp']:,}",
            "Status": c["status"],
            "Owner": c["owner"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_certifications(certs: list[dict]):
    st.subheader("🔐 Certification Register")
    st.caption("Bidirectional chase enabled · agent monitors expiry dates daily")

    rows = []
    for c in certs:
        icon = {"Valid": "✅", "Expiring Soon": "⚠️", "Expired": "❌"}.get(c["status"], "")
        rows.append({
            "Status": f"{icon} {c['status']}",
            "Supplier": c["supplier_name"],
            "Cert Type": c["type"],
            "Cert ID": c["cert_id"],
            "Expiry": c["expiry"],
            "Days Left": c["days_to_expiry"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### 📧 Generate chase email")
    chase_eligible = [c for c in certs if c["status"] in ("Expiring Soon", "Expired")]
    if not chase_eligible:
        st.info("No certs require chasing right now.")
        return

    col_a, col_b, col_c = st.columns(3)
    cert_choice = col_a.selectbox("Certification", chase_eligible,
                                    format_func=lambda c: f"{c['supplier_name']} — {c['type']}")
    lang = col_b.selectbox("Language", ["English", "Spanish"])
    if col_c.button("✍ Draft email", use_container_width=True):
        email = _draft_cert_chase_email(
            supplier_name=cert_choice["supplier_name"],
            cert_type=cert_choice["type"],
            cert_id=cert_choice["cert_id"],
            expiry_date=cert_choice["expiry"],
            days_to_expiry=cert_choice["days_to_expiry"],
            language=lang.lower(),
        )
        st.session_state["last_chase_email"] = email

    if "last_chase_email" in st.session_state:
        st.text_area("Draft (review before sending)", st.session_state["last_chase_email"], height=350)
        st.info("Drafted by Market Watcher agent — for internal review only.")


def _render_market_intel():
    items = get_market_intel(limit=20)
    st.subheader("📰 Market Intelligence Feed")
    st.caption("Agent-aggregated from Gartner, Forrester, IDC, FT, Reuters, internal Centrica systems")

    tag_color = {
        "analyst": "#0F2067", "news": "#9B2BF7",
        "regulation": "#B999F6", "internal": "#85DB9C",
    }
    for item in items:
        bg = tag_color.get(item.get("tag", "news"), "#DECFFF")
        st.markdown(
            f"""<div style="border-left:4px solid {bg};padding:8px 12px;background:#fafafa;border-radius:4px;margin-bottom:8px;">
                <div style="font-size:0.95rem;font-weight:bold;color:#0F2067;">{item['title']}</div>
                <div style="margin-top:4px;font-size:0.85rem;color:#444;">{item['snippet']}</div>
                <div style="margin-top:6px;font-size:0.75rem;color:#888;">
                    {item['source']} · {item['date']} · <span style="background:{bg};color:white;padding:1px 6px;border-radius:3px;">{item.get('tag', 'news').upper()}</span>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_vendor_360():
    suppliers = list_suppliers()
    options = {s["supplier_id"]: s["name"] for s in suppliers}
    supplier_id = st.selectbox("Select vendor", list(options.keys()),
                                format_func=lambda x: options[x])
    if not supplier_id:
        return

    result = get_supplier_360(supplier_id)
    if result["status"] != "ok":
        st.error(result["message"])
        return

    d = result["supplier"]
    st.markdown(f"### {d['name']}")

    tier_color = {"Strategic": "#0F2067", "Preferred": "#9B2BF7", "Approved": "#B999F6"}.get(d.get("tier"), "#B999F6")
    st.markdown(
        f"""<div>
            <span style="background:{tier_color};color:white;padding:3px 10px;border-radius:4px;font-weight:bold;font-size:0.85rem;">{d.get('tier', '')}</span>
            <span style="background:#85DB9C;color:#0F2067;padding:3px 10px;border-radius:4px;font-weight:bold;font-size:0.85rem;margin-left:6px;">{d.get('status', '')}</span>
            <span style="color:#666;margin-left:8px;font-size:0.85rem;">{d.get('subcategory', '')}</span>
        </div>""",
        unsafe_allow_html=True,
    )

    if d.get("products"):
        st.markdown(f"**Products in scope:** {' · '.join(d['products'])}")

    st.markdown("---")
    fin = d.get("financials", {})
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Revenue", f"${fin.get('revenue_usd_bn', 0):.1f}bn")
    c2.metric("Market cap", f"${fin.get('market_cap_usd_bn', 0):.0f}bn")
    c3.metric("EBITDA margin", f"{fin.get('ebitda_margin_pct', 0)}%")
    c4.metric("D&B risk", f"{fin.get('dnb_risk_score', '?')}/5")
    c5.metric("Credit rating", fin.get("credit_rating", "—"))

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### 🔐 Certifications")
        for cert in d.get("certifications", []):
            icon = {"Valid": "✅", "Expiring Soon": "⚠️", "Expired": "❌"}.get(cert["status"], "")
            st.markdown(f"{icon} **{cert['type']}** — expires {cert['expiry']}")

        st.markdown("#### 📜 Gartner positioning")
        g = d.get("gartner", {})
        if g:
            st.markdown(f"**{g.get('quadrant', '—')}** — *{g.get('report', '')}*")
            st.caption(f"Vision: {g.get('completeness_of_vision','?')}/5 · Execution: {g.get('ability_to_execute','?')}/5")

    with col_r:
        st.markdown("#### 🌱 ESG profile")
        esg = d.get("esg", {})
        for k, label in [
            ("re100_committed", "RE100 Committed"),
            ("living_wage_accredited", "Living Wage Accredited"),
            ("modern_slavery_statement", "Modern Slavery Statement"),
            ("scope3_reporting", "Scope 3 Reporting"),
        ]:
            val = esg.get(k)
            icon = "✅" if val else "❌"
            st.markdown(f"{icon} {label}")
        if esg.get("carbon_neutral_target"):
            st.markdown(f"📅 Carbon neutral target: **{esg['carbon_neutral_target']}**")
        if esg.get("ecovadis_score") is not None:
            st.markdown(f"⭐ Ecovadis: **{esg['ecovadis_score']}/100**")

    st.markdown("---")
    st.markdown("#### 📈 Analyst quotes")
    for q in d.get("analyst_quotes", []):
        st.markdown(f"> {q}")

    st.markdown("#### ⚠️ Risks")
    for risk in d.get("risks", []):
        st.markdown(f"- {risk_badge(risk['severity'])}  **{risk['type']}** — {risk['description']}",
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📄 Contract")
    contract = d.get("contract", {})
    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.metric("Ref", contract.get("ref", "—"))
    cc2.metric("Expiry", contract.get("expiry", "—"))
    cc3.metric("Value", f"£{contract.get('value_gbp', 0):,}")
    cc4.metric("Owner", contract.get("owner", "—"))
    st.caption(f"Payment terms: {contract.get('payment_terms', '—')} · Auto-renew: {contract.get('auto_renew', False)}")
