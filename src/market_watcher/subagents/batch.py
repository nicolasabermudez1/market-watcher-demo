"""Scheduled Batch Agent — Monday-morning intelligence digest."""

import json
from datetime import datetime
from pathlib import Path

from agents import Agent, Runner
from tenacity import retry, stop_after_attempt, wait_exponential

from market_watcher.config import MODEL_PRIMARY, FIXTURES_DIR
from market_watcher.tools.mock_services import (
    mock_supplier_360,
    mock_supplier_directory,
    mock_certification_register,
    mock_news_for_category,
    mock_pestle,
    mock_industry_risks,
    mock_regulations,
    mock_market_intel,
)
from market_watcher.tools.retrieval import semantic_retrieve
from market_watcher.tools.tracer import save_trace


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / "batch_agent.md"
    return prompt_path.read_text(encoding="utf-8")


def build_batch_agent() -> Agent:
    return Agent(
        name="MarketWatcherBatchAgent",
        model=MODEL_PRIMARY,
        instructions=_load_system_prompt(),
        tools=[
            mock_supplier_directory,
            mock_supplier_360,
            mock_certification_register,
            mock_news_for_category,
            mock_pestle,
            mock_industry_risks,
            mock_regulations,
            mock_market_intel,
            semantic_retrieve,
        ],
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def run_monday_scan(category: str = "Cloud Infrastructure") -> dict:
    """Run the batch Monday scan and return structured results."""
    agent = build_batch_agent()
    run_date = datetime.now().strftime("%Y-%m-%d")

    prompt = (
        f"Run the Monday-morning Market Watcher intelligence scan for the '{category}' category. "
        f"Today is {run_date}. "
        f"Pull supplier directory, market intel, industry risks, regulations, and certification register. "
        f"Synthesise findings into a structured JSON object with keys: "
        f"  - summary (2-3 sentence executive summary), "
        f"  - risk_count (int), "
        f"  - high_risks (list of short risk descriptions), "
        f"  - cert_alerts (list of '<Supplier> — <CertType> (expires <date>)' strings), "
        f"  - news_sources (list of source names cited), "
        f"  - top_actions (list of 3-5 concrete next-step actions for the head of procurement). "
        f"Return JSON only. Do not generate any documents."
    )

    tool_calls_log = []

    try:
        result = Runner.run_sync(agent, prompt)
        raw_output = result.final_output

        # Parse JSON output if the agent returned it
        parsed = {}
        try:
            if "```json" in raw_output:
                raw_output = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                raw_output = raw_output.split("```")[1].split("```")[0].strip()
            parsed = json.loads(raw_output)
        except Exception:
            parsed = {"summary": raw_output, "risk_count": 0,
                      "high_risks": [], "news_sources": [], "cert_alerts": [], "top_actions": []}

        # Collect tool calls from run context — defensive across SDK versions
        try:
            messages = getattr(result, "new_messages", None) or getattr(result, "new_items", None) or []
            for msg in messages:
                tcs = getattr(msg, "tool_calls", None) or []
                for tc in tcs:
                    fn = getattr(tc, "function", None)
                    tool_calls_log.append({
                        "tool": getattr(fn, "name", str(tc)) if fn else str(tc),
                        "input": getattr(fn, "arguments", "") if fn else "",
                        "status": "ok",
                    })
        except Exception:
            pass  # trace logging is nice-to-have, never block the scan

        save_trace(
            agent_name="batch",
            inputs={"category": category, "run_date": run_date},
            outputs=parsed,
            tool_calls=tool_calls_log,
        )

        return {"status": "ok", **parsed}

    except Exception as e:
        save_trace(
            agent_name="batch",
            inputs={"category": category, "run_date": run_date},
            outputs={"error": str(e)},
            tool_calls=tool_calls_log,
        )
        return {"status": "error", "message": str(e)}
