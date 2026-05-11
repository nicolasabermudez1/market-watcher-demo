"""Tab 2 — Supplier & Category Dashboard."""

import json
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from market_watcher.config import DEMO_SUPPLIERS, FIXTURES_DIR
from market_watcher.ui.styles import header_html, risk_badge
from market_watcher.tools.mock_services import (
    get_supplier_360, get_certification_register
)
from market_watcher.tools.document_gen import _draft_cert_chase_email


SUPPLIER_LABELS = {
    "microsoft": "Microsoft Azure",
    "aws": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
}


def render():
    st.markdown(header_html(
        "Supplier & Category Dashboard",
        "Cloud Infrastructure · 3 PSL Suppliers · Live mock data"
    ), unsafe_allow_html=True)

    view = st.radio("View", ["Category Overview", "Supplier 360"], horizontal=True)

    if view == "Category Overview":
        _render_category_overview()
    else:
        _render_supplier_360()


def _render_category_overview():
    st.subheader("Category Snapshot — Cloud Infrastructure")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total YTD Spend", "£3.1m", "+8% vs prior year")
    col2.metric("Active Suppliers", "3", "PSL-approved")
    col3.metric("Open Risks", "7", "2 High priority")
    col4.metric("Cert Compliance", "60%", "-40% from target", delta_color="inverse")

    st.markdown("---")

    # Spend by supplier (bar)
    try:
        import pandas as pd
        spend_path = FIXTURES_DIR / "spend_by_category.csv"
        df = pd.read_csv(spend_path)
        by_supplier = df.groupby("supplier_name")["spend_gbp"].sum().reset_index()
        by_supplier.columns = ["Supplier", "Spend (£)"]

        st.subheader("YTD Spend by Supplier")
        st.bar_chart(by_supplier.set_index("Supplier"), color="#0F2067")

        st.subheader("Monthly Spend Trend")
        pivot = df.pivot_table(index="month", columns="supplier_name", values="spend_gbp", aggfunc="sum")
        st.line_chart(pivot)
    except Exception as e:
        st.info(f"Spend chart unavailable: {e}")

    st.markdown("---")

    # Certification register
    st.subheader("Certification Register")
    certs = get_certification_register()
    _render_cert_table(certs)


def _render_cert_table(certs: list):
    import pandas as pd
    rows = []
    for c in certs:
        status_icon = {"Valid": "✅", "Expiring Soon": "⚠️", "Expired": "❌"}.get(c["status"], "")
        rows.append({
            "Supplier": c["supplier_name"],
            "Cert Type": c["type"],
            "Cert ID": c["cert_id"],
            "Expiry": c["expiry"],
            "Days Left": c["days_to_expiry"],
            "Status": f"{status_icon} {c['status']}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_supplier_360():
    supplier_id = st.selectbox(
        "Select Supplier",
        options=DEMO_SUPPLIERS,
        format_func=lambda x: SUPPLIER_LABELS.get(x, x),
    )

    if not supplier_id:
        return

    try:
        fixture_path = FIXTURES_DIR / "suppliers" / "cloud_infrastructure" / f"{supplier_id}.json"
        with open(fixture_path) as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"Could not load supplier data: {e}")
        return

    st.markdown(f"### {data['name']}")
    status_color = "#85DB9C" if data["status"] == "Active PSL" else "#B999F6"
    st.markdown(f'<span style="background:{status_color};color:#0F2067;padding:3px 10px;border-radius:4px;font-weight:bold;">{data["status"]}</span>', unsafe_allow_html=True)
    st.markdown("")

    col1, col2, col3, col4 = st.columns(4)
    fin = data.get("financials", {})
    col1.metric("Revenue", f"${fin.get('revenue_usd_bn', 0):.1f}bn USD")
    col2.metric("EBITDA Margin", f"{fin.get('ebitda_margin_pct', 0)}%")
    col3.metric("D&B Risk Score", f"{fin.get('dnb_risk_score', '?')} / 5")
    col4.metric("Credit Rating", fin.get("credit_rating", "—"))

    st.markdown("---")

    # Certifications
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Certifications")
        for cert in data.get("certifications", []):
            icon = {"Valid": "✅", "Expiring Soon": "⚠️", "Expired": "❌"}.get(cert["status"], "")
            st.markdown(f"{icon} **{cert['type']}** — expires {cert['expiry']} ({cert['status']})")

    with col_right:
        st.subheader("ESG Profile")
        esg = data.get("esg", {})
        for key, label in [
            ("re100_committed", "RE100 Committed"),
            ("carbon_neutral_target", "Carbon Neutral Target"),
            ("living_wage_accredited", "Living Wage Accredited"),
            ("modern_slavery_statement", "Modern Slavery Statement"),
            ("scope3_reporting", "Scope 3 Reporting"),
        ]:
            val = esg.get(key)
            if isinstance(val, bool):
                icon = "✅" if val else "❌"
                st.markdown(f"{icon} {label}")
            else:
                st.markdown(f"📅 {label}: **{val}**")

    st.markdown("---")

    # Risks
    st.subheader("Risk Register")
    for risk in data.get("risks", []):
        severity = risk.get("severity", "Low")
        st.markdown(
            f"{risk_badge(severity)} **{risk['type']}** — {risk['description']}",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Contract
    st.subheader("Contract Details")
    contract = data.get("contract", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Contract Ref", contract.get("ref", "—"))
    c2.metric("Expiry", contract.get("expiry", "—"))
    c3.metric("Value", f"£{contract.get('value_gbp', 0):,}")
    st.markdown(f"**Owner:** {contract.get('owner', '—')}  ·  **Payment Terms:** {contract.get('payment_terms', '—')}")

    st.markdown("---")

    # Spend
    st.subheader("Spend")
    spend = data.get("spend", {})
    s1, s2 = st.columns(2)
    s1.metric("YTD Spend", f"£{spend.get('ytd_gbp', 0):,}")
    s2.metric("Prior Year", f"£{spend.get('prior_year_gbp', 0):,}")

    st.markdown("---")

    # Cert chase
    st.subheader("Chase Expiring Certifications")
    expiring_certs = [c for c in data.get("certifications", []) if c["status"] in ("Expiring Soon", "Expired")]
    if not expiring_certs:
        st.success("No certifications require chasing for this supplier.")
    else:
        cert_choice = st.selectbox("Select cert to chase", [c["type"] for c in expiring_certs])
        lang = st.radio("Email language", ["English", "Spanish"], horizontal=True)
        if st.button("Generate Chase Email"):
            selected = next(c for c in expiring_certs if c["type"] == cert_choice)
            today = date.today()
            days_left = (date.fromisoformat(selected["expiry"]) - today).days
            email_body = _draft_cert_chase_email(
                supplier_name=data["name"],
                cert_type=selected["type"],
                cert_id=selected["cert_id"],
                expiry_date=selected["expiry"],
                days_to_expiry=days_left,
                language=lang.lower(),
            )
            st.session_state[f"email_{supplier_id}_{cert_choice}"] = email_body

        key = f"email_{supplier_id}_{cert_choice}"
        if key in st.session_state:
            st.text_area("Draft Email (review before sending)", st.session_state[key], height=350)
            st.info("This email was drafted by the Market Watcher Agent — review before sending.")
