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
from market_watcher.tools.document_gen import generate_weekly_digest
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
            generate_weekly_digest,
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
        f"Search for recent news about Microsoft Azure, AWS, and Google Cloud Platform related to "
        f"procurement risk, certifications, ESG, market changes, and UK regulatory updates. "
        f"Retrieve 360 profiles for all three suppliers. Check the certification register. "
        f"Compile risks and generate the weekly digest Word document. "
        f"Return your result as a JSON object with keys: digest_path, risk_count, high_risks, "
        f"news_sources, cert_alerts, summary."
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
            parsed = {"summary": raw_output, "digest_path": "", "risk_count": 0,
                      "high_risks": [], "news_sources": [], "cert_alerts": []}

        # Collect tool calls from run context
        for msg in result.new_messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls_log.append({
                        "tool": tc.function.name if hasattr(tc, "function") else str(tc),
                        "input": tc.function.arguments if hasattr(tc, "function") else "",
                        "status": "ok",
                    })

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
