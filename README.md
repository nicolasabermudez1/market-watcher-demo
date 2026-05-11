# Market Watcher — Centrica Procurement Intelligence Demo

A working demo of the Market Watcher agent for Centrica Procurement, showcasing
AI-powered supplier monitoring, certification management, and self-serve buying.

**Category in scope:** Cloud Infrastructure (Microsoft Azure · AWS · GCP)

---

## Quick Start (< 5 minutes)

### 1. Prerequisites
- Python 3.12+ installed
- `uv` package manager: `pip install uv`
- A Google Gemini API key (get a free one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey))

### 2. Setup (first time only)

```bash
# From the market-watcher-demo/ directory:
uv venv
uv pip install -e .
cp .env.example .env
```

Open `.env` and paste your key:
```
GEMINI_API_KEY=AIzaSy...
```

That is the **only required step**.

### 3. Run the demo

```bash
just demo
# or without just:
uv run streamlit run src/market_watcher/main.py
```

The UI opens at **http://localhost:8501**

---

## Demo Walkthrough

Walk through the three tabs left to right:

### Tab 1 — Monday Digest
Click **Run Monday Scan** to trigger the intelligence agent. It will:
- Pull recent news on Microsoft Azure, AWS, and GCP from the curated mock feed
- Retrieve 360 supplier profiles and check the certification register
- Rank risks by severity (High / Medium / Low)
- Generate a Centrica-branded Word document digest in `outputs/`

### Tab 2 — Supplier Dashboard
- **Category Overview**: spend charts, monthly trends, certification register
- **Supplier 360**: select a supplier to see financials, certifications, ESG profile, risks, and contract details
- **Chase Email**: generate a certification expiry chase email (English or Spanish) for any expiring cert

### Tab 3 — Buyer Guide
- Use the **sidebar sliders** to set criteria weights — the ranking updates in real time
- Chat with the Buyer Guide agent: describe what you need and it will shortlist PSL suppliers
- Try raising the ESG weight and watch GCP move to rank 1

---

## CLI Usage

```bash
# Run the Monday scan headlessly
just cli
# or: uv run python -m market_watcher.cli scan

# Ask the Buyer Guide a question
uv run python -m market_watcher.cli ask "I need cloud compute for a 3-month data migration project"

# Show the certification register
uv run python -m market_watcher.cli certs

# Show PSL ranking with custom weights
uv run python -m market_watcher.cli rank --esg 0.5 --quality 0.3 --price 0.2
```

---

## Inspect Traces

Every agent run writes a JSON trace to `data/runs/`:

```bash
just trace
# or: uv run python -m market_watcher.tools.trace_viewer
```

OpenAI platform traces also appear automatically at [platform.openai.com/traces](https://platform.openai.com/traces).

---

## Reset State

```bash
just reset
# Clears data/runs/, data/state.sqlite, outputs/
# Fixture data in data/fixtures/ is NOT modified
```

---

## Run Smoke Tests

```bash
just test
# or: uv run pytest tests/ -v
```

---

## Common Errors

| Error | Fix |
|-------|-----|
| `GEMINI_API_KEY not set` | Copy `.env.example` → `.env` and paste your key from aistudio.google.com/apikey |
| `Gemini rate-limited` | Tenacity retries 3× automatically — wait a minute and try again |
| `Tool failed` | The Streamlit UI shows the failing tool name — check `data/runs/` for the trace |
| `just: command not found` | Install with `cargo install just` or run `uv run streamlit run src/market_watcher/main.py` directly |
| `chromadb` errors | Set `use_chroma = false` in `config.toml` — the demo runs without it |

---

## Project Structure

```
market-watcher-demo/
├── .env                  # Your OpenAI key (not committed)
├── .env.example          # Template — copy to .env
├── config.toml           # Mock/real tool flags + model names
├── justfile              # Run targets: demo / reset / trace / test
├── pyproject.toml        # Dependencies (uv-managed)
├── src/market_watcher/
│   ├── main.py           # Streamlit entry-point
│   ├── cli.py            # CLI variant
│   ├── config.py         # Config loader
│   ├── orchestrator.py   # Agent wiring
│   ├── subagents/
│   │   ├── batch.py      # Monday scan agent
│   │   └── query.py      # Buyer Guide agent
│   ├── tools/
│   │   ├── mock_services.py   # Supplier/PSL/cert mock tools
│   │   ├── document_gen.py    # Word digest + email generator
│   │   ├── retrieval.py       # Chroma vector search
│   │   ├── web_search.py      # Web search tool
│   │   └── tracer.py          # Run trace logger
│   ├── prompts/
│   │   ├── batch_agent.md     # Batch agent system prompt
│   │   └── query_agent.md     # Query agent system prompt
│   └── ui/
│       ├── styles.py           # Centrica CSS + helpers
│       ├── tab_digest.py       # Monday Digest tab
│       ├── tab_dashboard.py    # Supplier Dashboard tab
│       └── tab_buyer_guide.py  # Buyer Guide tab
├── data/
│   ├── fixtures/         # Mock master data (committed)
│   └── runs/             # Per-run trace JSON (gitignored)
├── outputs/              # Generated Word/PDF (gitignored)
└── tests/
    └── test_smoke.py     # Smoke tests
```

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.12+ |
| Package manager | `uv` |
| Agent framework | `openai-agents` (pointed at Gemini's OpenAI-compatibility endpoint) |
| LLM | `gemini-2.5-flash` (primary), `gemini-2.5-flash-lite` (fast lanes) |
| UI | Streamlit ≥ 1.36 |
| Data store | SQLite + JSON fixtures + Chroma |
| News source | Curated mock feed (10 items); Brave Search fallback optional |
| Branding | Centrica navy `#0F2067` · mint `#85DB9C` · lavender `#B999F6` |

---

*Centrica Procurement Transformation · Workstream 1 — Processes · Market Watcher Demo*
