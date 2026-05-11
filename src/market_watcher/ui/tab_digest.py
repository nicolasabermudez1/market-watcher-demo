"""Tab 1 — Monday Morning Digest with agent theatre."""

from datetime import datetime
from pathlib import Path

import streamlit as st

from market_watcher.config import DEMO_CATEGORY, OUTPUTS_DIR
from market_watcher.ui.styles import header_html, risk_badge
from market_watcher.ui.agent_theatre import stream_with_progress


def render():
    st.markdown(header_html(
        "Monday Morning Intelligence Digest",
        f"Market Watcher · {DEMO_CATEGORY} · {datetime.now().strftime('%A %d %B %Y')}"
    ), unsafe_allow_html=True)

    st.markdown("""
    The Market Watcher agent runs every Monday at 06:00 UTC. It pulls **vendor 360 profiles**,
    **Gartner / Forrester analyst views**, **Ariba spend data**, **certification register**,
    **industry regulations**, and **PESTLE intelligence** — then produces a Centrica-branded Word digest.
    """)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("▶  Run Monday Scan now", key="run_scan", use_container_width=True, type="primary"):
            _run_scan()
    with col2:
        digests = sorted(OUTPUTS_DIR.glob("*_digest.docx"), reverse=True) if OUTPUTS_DIR.exists() else []
        st.metric("Digests generated", len(digests))

    if "digest_result" in st.session_state:
        _render_results(st.session_state["digest_result"])

    st.markdown("---")
    st.subheader("📄 Recent digests")
    digests = sorted(OUTPUTS_DIR.glob("*_digest.docx"), reverse=True) if OUTPUTS_DIR.exists() else []
    if digests:
        for d in digests[:5]:
            col_a, col_b, col_c = st.columns([4, 1, 1])
            col_a.markdown(f"📄 `{d.name}`")
            col_b.markdown(f"{d.stat().st_size // 1024} KB")
            with open(d, "rb") as f:
                col_c.download_button("⬇ Download", f, file_name=d.name, key=f"dl_{d.name}",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.info("No digests generated yet. Click ▶ Run Monday Scan above.")


def _run_scan():
    stream_with_progress(track="scan", message_delay=0.35)

    # Now actually run the agent (after theatre completes — fast and reliable)
    try:
        from market_watcher.subagents.batch import run_monday_scan
        with st.spinner("Finalising with Gemini..."):
            result = run_monday_scan(DEMO_CATEGORY)
        st.session_state["digest_result"] = result
        if result.get("status") == "ok":
            st.success("✅ Scan complete — digest generated.")
        else:
            st.error(f"Agent error: {result.get('message', 'unknown')}")
    except Exception as e:
        st.session_state["digest_result"] = {"status": "error", "message": str(e)}
        st.error(f"Agent error: {e}")


def _render_results(result: dict):
    if result.get("status") == "error":
        st.error(f"Last scan failed: {result.get('message', '')}")
        return

    st.markdown("---")
    st.subheader("📈 This week's findings")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Risks", result.get("risk_count", 0))
    c2.metric("High Priority", len(result.get("high_risks", [])))
    c3.metric("News Sources", len(result.get("news_sources", [])))
    c4.metric("Cert Alerts", len(result.get("cert_alerts", [])))

    if result.get("summary"):
        st.info(result["summary"])

    if result.get("high_risks"):
        st.markdown("#### 🔴 High Priority Risks")
        for risk in result["high_risks"]:
            st.markdown(f"- {risk_badge('High')}  {risk}", unsafe_allow_html=True)

    if result.get("cert_alerts"):
        st.markdown("#### ⚠️ Certification Alerts")
        for alert in result["cert_alerts"]:
            st.warning(alert)

    if result.get("news_sources"):
        st.markdown(f"**Sources cited:** {' · '.join(result['news_sources'][:6])}")

    if result.get("digest_path"):
        p = Path(result["digest_path"])
        if p.exists():
            with open(p, "rb") as f:
                st.download_button(
                    "⬇  Download digest (Word)", data=f, file_name=p.name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
