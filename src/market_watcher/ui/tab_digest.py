"""Tab 1 — Monday Morning Digest."""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from market_watcher.config import DEMO_CATEGORY, OUTPUTS_DIR
from market_watcher.ui.styles import header_html, risk_badge


def render():
    st.markdown(header_html(
        "Monday Morning Intelligence Digest",
        f"Market Watcher Agent · {DEMO_CATEGORY} · {datetime.now().strftime('%A %d %B %Y')}"
    ), unsafe_allow_html=True)

    st.markdown("""
    The agent runs a live scan combining **web search**, **supplier 360 profiles**, and the
    **certification register** to produce a Centrica-branded Word document digest every Monday morning.
    """)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("▶  Run Monday Scan", key="run_scan", use_container_width=True):
            _run_scan()

    with col2:
        digests = sorted(OUTPUTS_DIR.glob("*_digest.docx"), reverse=True) if OUTPUTS_DIR.exists() else []
        if digests:
            st.success(f"{len(digests)} digest(s) generated")

    # Show previous results if available
    if "digest_result" in st.session_state:
        _render_results(st.session_state["digest_result"])

    # List generated files
    st.markdown("---")
    st.subheader("Generated Digests")
    digests = sorted(OUTPUTS_DIR.glob("*_digest.docx"), reverse=True) if OUTPUTS_DIR.exists() else []
    if digests:
        for d in digests[:5]:
            st.markdown(f"📄 `{d.name}` — {d.stat().st_size // 1024} KB")
    else:
        st.info("No digests generated yet. Click 'Run Monday Scan' to start.")


def _run_scan():
    category = DEMO_CATEGORY
    progress_container = st.empty()
    log_container = st.empty()

    steps = [
        "Searching web for latest market intelligence...",
        "Retrieving Microsoft Azure supplier profile...",
        "Retrieving AWS supplier profile...",
        "Retrieving Google Cloud Platform profile...",
        "Checking certification register...",
        "Ranking risks by severity...",
        "Generating Centrica-branded Word digest...",
    ]

    with st.spinner("Market Watcher agent running..."):
        progress = st.progress(0)
        log_lines = []
        for i, step in enumerate(steps):
            log_lines.append(f"✓ {step}")
            log_container.code("\n".join(log_lines), language=None)
            progress.progress((i + 1) / len(steps))
            time.sleep(0.4)

        try:
            from market_watcher.subagents.batch import run_monday_scan
            result = run_monday_scan(category)
            st.session_state["digest_result"] = result
            progress.empty()
            log_container.empty()

            if result.get("status") == "ok":
                st.success("Scan complete — digest generated!")
            else:
                st.error(f"Scan failed: {result.get('message', 'Unknown error')}")

        except Exception as e:
            progress.empty()
            log_container.empty()
            st.error(f"Agent error: {e}")
            st.session_state["digest_result"] = {
                "status": "error", "message": str(e),
                "summary": "Agent encountered an error — see details above.",
                "high_risks": [], "news_sources": [], "cert_alerts": [], "risk_count": 0,
                "digest_path": "",
            }


def _render_results(result: dict):
    if result.get("status") == "error":
        st.error(f"Last scan failed: {result.get('message', '')}")
        return

    st.markdown("---")
    st.subheader("Latest Scan Results")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Risks", result.get("risk_count", 0))
    col2.metric("High Priority", len(result.get("high_risks", [])))
    col3.metric("News Sources", len(result.get("news_sources", [])))
    col4.metric("Cert Alerts", len(result.get("cert_alerts", [])))

    if result.get("summary"):
        st.markdown(f"> {result['summary']}")

    if result.get("high_risks"):
        st.markdown("#### High Priority Risks")
        for risk in result["high_risks"]:
            st.markdown(f"- {risk_badge('High')} {risk}", unsafe_allow_html=True)

    if result.get("cert_alerts"):
        st.markdown("#### Certification Alerts")
        for alert in result["cert_alerts"]:
            st.warning(f"⚠ {alert}")

    if result.get("news_sources"):
        st.markdown(f"**Sources used:** {', '.join(result['news_sources'])}")

    if result.get("digest_path"):
        p = Path(result["digest_path"])
        if p.exists():
            with open(p, "rb") as f:
                st.download_button(
                    label=f"⬇  Download {p.name}",
                    data=f,
                    file_name=p.name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
