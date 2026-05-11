"""Run-trace JSON logger — records every agent execution."""

import json
import time
from datetime import datetime
from pathlib import Path

from market_watcher.config import RUNS_DIR


def save_trace(agent_name: str, inputs: dict, outputs: dict, tool_calls: list, tokens: dict | None = None) -> str:
    """Write a run trace JSON file. Returns the file path."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{agent_name}.json"
    filepath = RUNS_DIR / filename

    trace = {
        "run_id": ts,
        "agent": agent_name,
        "timestamp": datetime.now().isoformat(),
        "inputs": inputs,
        "tool_calls": tool_calls,
        "outputs": outputs,
        "tokens": tokens or {},
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2, default=str)
    return str(filepath)


def load_latest_trace() -> dict | None:
    """Load the most recent run trace file."""
    traces = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not traces:
        return None
    with open(traces[0]) as f:
        return json.load(f)
