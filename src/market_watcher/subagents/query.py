"""On-Demand Query Agent — Buyer Guide conversational interface."""

from pathlib import Path
from agents import Agent, Runner
from tenacity import retry, stop_after_attempt, wait_exponential

from market_watcher.config import MODEL_PRIMARY
from market_watcher.tools.mock_services import (
    mock_supplier_360, mock_psl_search, mock_supplier_directory, mock_market_intel
)
from market_watcher.tools.retrieval import semantic_retrieve
from market_watcher.tools.tracer import save_trace


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / "query_agent.md"
    return prompt_path.read_text(encoding="utf-8")


def build_query_agent() -> Agent:
    # Deliberately excludes WebSearchTool — PSL-only
    return Agent(
        name="MarketWatcherQueryAgent",
        model=MODEL_PRIMARY,
        instructions=_load_system_prompt(),
        tools=[
            mock_psl_search,
            mock_supplier_360,
            mock_supplier_directory,
            mock_market_intel,
            semantic_retrieve,
        ],
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def run_buyer_query(user_message: str, conversation_history: list | None = None) -> dict:
    """Run a single Buyer Guide query turn. Returns agent response text and updated history."""
    agent = build_query_agent()

    messages = conversation_history or []
    messages.append({"role": "user", "content": user_message})

    tool_calls_log = []

    try:
        result = Runner.run_sync(agent, messages)
        response_text = result.final_output

        for msg in result.new_messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls_log.append({
                        "tool": tc.function.name if hasattr(tc, "function") else str(tc),
                        "input": tc.function.arguments if hasattr(tc, "function") else "",
                        "status": "ok",
                    })

        messages.append({"role": "assistant", "content": response_text})

        save_trace(
            agent_name="query",
            inputs={"user_message": user_message},
            outputs={"response": response_text},
            tool_calls=tool_calls_log,
        )

        return {"status": "ok", "response": response_text, "history": messages}

    except Exception as e:
        save_trace(
            agent_name="query",
            inputs={"user_message": user_message},
            outputs={"error": str(e)},
            tool_calls=tool_calls_log,
        )
        return {"status": "error", "message": str(e), "history": messages}
