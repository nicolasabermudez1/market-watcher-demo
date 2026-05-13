"""Agent activity theatre — streams realistic 'agent is working' messages to Streamlit.

Pure visual element: makes it visible to the user that the Market Watcher agent is
querying Gartner, pulling Ariba spend data, scanning supplier news, etc. The actual
data is loaded from fixtures, but the streamed messages let the user *see* the agent
doing its job rather than staring at a blank spinner.
"""

import random
import time
from typing import Sequence

import streamlit as st


# Activity messages tagged with a category emoji + short delay (seconds)
ACTIVITY_LIBRARY: dict[str, list[tuple[str, str]]] = {
    "scan": [
        ("🔍", "Spawning Market Watcher agent (Gemini 2.5)..."),
        ("📡", "Querying Gartner Magic Quadrant — Enterprise Application Software 2026..."),
        ("📡", "Querying Gartner Hype Cycle — Generative AI for Enterprise..."),
        ("📡", "Pulling Forrester Wave reports (Source-to-Pay, ITSM, CRM)..."),
        ("💼", "Connecting to Dun & Bradstreet — pulling D&B Risk Scores and financial-stability ratings..."),
        ("💼", "D&B: cross-referencing UCC filings and corporate-family hierarchy for 9 PSL vendors..."),
        ("📈", "Connecting to Bloomberg Terminal — pulling vendor market cap, credit spreads, earnings calls..."),
        ("📈", "Bloomberg: scanning M&A, activist-investor and PE-acquisition signals..."),
        ("🏷️", "Connecting to Achilles — pulling supplier pre-qualification status and audit scores..."),
        ("🏷️", "Achilles: verifying UVDB / JOSCAR membership and compliance evidence..."),
        ("🇬🇧", "Connecting to Companies House — pulling UK registration, filings, charges..."),
        ("🇬🇧", "Companies House: checking PSC (Persons with Significant Control) and director changes..."),
        ("📊", "Connecting to SAP Ariba — extracting IT Software category spend..."),
        ("📊", "Pulling Spend Cube — last 12 months by sub-category..."),
        ("📋", "Reading JD Edwards contract register — 47 active agreements..."),
        ("🌐", "Scanning Reuters, FT, The Register, Diginomica for vendor news..."),
        ("🧾", "Loading Ecovadis sustainability scorecards for 9 PSL vendors..."),
        ("🔐", "Querying certification register — ISO 27001, SOC 2, Cyber Essentials..."),
        ("⚖️", "Checking EU AI Act & UK AI Bill applicability matrix..."),
        ("🌍", "Refreshing PESTLE factor library from Centrica Strategy intranet..."),
        ("⚠️", "Flagging contracts expiring within 90 days..."),
        ("🧠", "Synthesising findings with Gemini 2.5 Flash..."),
        ("✅", "Findings ready — rendering visuals."),
    ],
    "dashboard": [
        ("📊", "Refreshing Ariba spend cube (live connection)..."),
        ("📋", "Pulling 8 vendor 360 profiles from supplier master..."),
        ("📡", "Updating Gartner quadrant positions..."),
        ("🧾", "Loading Ecovadis + D&B risk overlays..."),
        ("🔐", "Re-running certification expiry check..."),
        ("✅", "Dashboard refreshed."),
    ],
    "ranking": [
        ("⚖️", "Re-weighting PSL ranking with new criteria..."),
        ("📊", "Querying supplier scorecard for 8 vendors..."),
        ("🧠", "Computing weighted-sum rank..."),
    ],
    "vendor_scout": [
        ("🔍", "Agent: scouting net-new vendors for IT Software..."),
        ("🌐", "Scanning G2 Crowd, Capterra, Gartner Peer Insights..."),
        ("📡", "Filtering for UK presence + Cyber Essentials Plus..."),
        ("🧾", "Cross-referencing modern slavery & ESG attestations..."),
        ("📋", "Adding 3 candidate vendors to onboarding pipeline..."),
        ("✅", "Vendor scout complete."),
    ],
}


def stream(track: str = "scan", message_delay: float = 0.35, slot=None) -> None:
    """Stream activity messages for the given track to a Streamlit placeholder.

    Args:
        track: which activity library to use ("scan", "dashboard", "ranking", "vendor_scout").
        message_delay: seconds between messages. Use 0 for no delay (testing).
        slot: optional st.empty() placeholder. If None, creates one.
    """
    activities = ACTIVITY_LIBRARY.get(track, ACTIVITY_LIBRARY["scan"])
    if slot is None:
        slot = st.empty()

    lines: list[str] = []
    for icon, msg in activities:
        lines.append(f"{icon}  {msg}")
        slot.markdown(
            f"""<div style="background:#0F2067;color:#85DB9C;padding:10px 14px;
                          border-radius:8px;font-family:monospace;font-size:0.85rem;
                          max-height:240px;overflow:auto;line-height:1.7;">
                {'<br>'.join(lines)}
            </div>""",
            unsafe_allow_html=True,
        )
        time.sleep(message_delay + random.uniform(-0.05, 0.1))


def stream_with_progress(track: str = "scan", message_delay: float = 0.35) -> None:
    """Same as stream() but with a progress bar alongside."""
    activities = ACTIVITY_LIBRARY.get(track, ACTIVITY_LIBRARY["scan"])
    progress = st.progress(0, text="Market Watcher agent starting up...")
    log_slot = st.empty()
    lines: list[str] = []

    for i, (icon, msg) in enumerate(activities):
        lines.append(f"{icon}  {msg}")
        log_slot.markdown(
            f"""<div style="background:#0F2067;color:#85DB9C;padding:10px 14px;
                          border-radius:8px;font-family:monospace;font-size:0.85rem;
                          max-height:280px;overflow:auto;line-height:1.7;">
                {'<br>'.join(lines)}
            </div>""",
            unsafe_allow_html=True,
        )
        progress.progress((i + 1) / len(activities), text=msg)
        time.sleep(message_delay + random.uniform(-0.05, 0.15))

    progress.empty()
