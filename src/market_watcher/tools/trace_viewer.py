"""CLI trace viewer — pretty-prints the latest run trace."""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import print as rprint

from market_watcher.tools.tracer import load_latest_trace


def main(path: str | None = None) -> None:
    console = Console()
    if path:
        with open(path) as f:
            trace = json.load(f)
    else:
        trace = load_latest_trace()

    if not trace:
        console.print("[bold red]No trace files found in data/runs/[/bold red]")
        return

    console.print(f"\n[bold #0F2067]Category Watcher — Run Trace[/bold #0F2067]")
    console.print(f"Agent: [bold]{trace['agent']}[/bold]  ·  Run ID: {trace['run_id']}  ·  {trace['timestamp']}\n")

    if trace.get("tool_calls"):
        table = Table(title="Tool Calls", header_style="bold #0F2067")
        table.add_column("Tool", style="#B999F6")
        table.add_column("Input Summary", max_width=60)
        table.add_column("Status")
        for tc in trace["tool_calls"]:
            table.add_row(tc.get("tool", ""), str(tc.get("input", ""))[:80], tc.get("status", "ok"))
        console.print(table)

    if trace.get("tokens"):
        console.print(f"\n[dim]Tokens — prompt: {trace['tokens'].get('prompt_tokens', '?')}  "
                      f"completion: {trace['tokens'].get('completion_tokens', '?')}  "
                      f"total: {trace['tokens'].get('total_tokens', '?')}[/dim]")

    if trace.get("outputs"):
        console.print(f"\n[bold]Output:[/bold] {str(trace['outputs'])[:300]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
