"""Headless CLI variant — runs the Monday scan and Buyer Guide from the terminal."""

import json
import os
import sys
from datetime import datetime

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import print as rprint

load_dotenv()

app = typer.Typer(help="Category Watcher CLI — Centrica Procurement Intelligence Agent")
console = Console()


def _check_api_key():
    if not os.environ.get("GEMINI_API_KEY"):
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not set. Get a key from https://aistudio.google.com/apikey and add it to .env.")
        raise typer.Exit(1)


@app.command()
def scan(category: str = typer.Option("Cloud Infrastructure", help="Category to scan")):
    """Run the Monday-morning intelligence scan."""
    _check_api_key()
    console.print(f"\n[bold #0F2067]Category Watcher[/bold #0F2067] — Running Monday scan for [bold]{category}[/bold]\n")

    from market_watcher.subagents.batch import run_monday_scan
    result = run_monday_scan(category)

    if result.get("status") == "error":
        console.print(f"[bold red]Scan failed:[/bold red] {result['message']}")
        raise typer.Exit(1)

    console.print(f"[bold #85DB9C]✓ Scan complete[/bold #85DB9C]")
    console.print(f"\n[bold]Summary:[/bold] {result.get('summary', 'No summary')}")
    console.print(f"Risks: [bold]{result.get('risk_count', 0)}[/bold] total, "
                  f"[bold #9B2BF7]{len(result.get('high_risks', []))}[/bold #9B2BF7] high")

    if result.get("digest_path"):
        console.print(f"\n[bold]Digest saved to:[/bold] {result['digest_path']}")


@app.command()
def ask(message: str = typer.Argument(..., help="Question to ask the Buyer Guide")):
    """Ask the Buyer Guide a question."""
    _check_api_key()
    console.print(f"\n[bold #0F2067]Buyer Guide[/bold #0F2067] — {message}\n")

    from market_watcher.subagents.query import run_buyer_query
    result = run_buyer_query(message)

    if result.get("status") == "error":
        console.print(f"[bold red]Error:[/bold red] {result['message']}")
        raise typer.Exit(1)

    console.print(result["response"])


@app.command()
def certs():
    """Show the certification register."""
    from market_watcher.tools.mock_services import _load_certifications
    from datetime import date

    certs_data = _load_certifications()
    today = date.today()
    for cert in certs_data:
        exp = date.fromisoformat(cert["expiry"])
        cert["days_to_expiry"] = (exp - today).days
        cert["status"] = "Expired" if cert["days_to_expiry"] < 0 else (
            "Expiring Soon" if cert["days_to_expiry"] <= 90 else "Valid")

    table = Table(title="Certification Register", header_style="bold #0F2067")
    table.add_column("Supplier", style="#0F2067")
    table.add_column("Cert Type")
    table.add_column("Expiry")
    table.add_column("Days Left")
    table.add_column("Status")

    status_styles = {"Valid": "#85DB9C", "Expiring Soon": "#B999F6", "Expired": "#9B2BF7"}
    for cert in certs_data:
        style = status_styles.get(cert["status"], "")
        table.add_row(
            cert["supplier_name"], cert["type"], cert["expiry"],
            str(cert["days_to_expiry"]),
            f"[{style}]{cert['status']}[/{style}]" if style else cert["status"],
        )
    console.print(table)


@app.command()
def rank(
    price: float = typer.Option(0.25),
    quality: float = typer.Option(0.30),
    esg: float = typer.Option(0.15),
    speed: float = typer.Option(0.15),
    payment: float = typer.Option(0.05),
    support: float = typer.Option(0.10),
):
    """Show PSL ranking with given criteria weights."""
    weights = {"price": price, "quality": quality, "esg": esg,
               "delivery_speed": speed, "payment_terms": payment, "support": support}
    from market_watcher.tools.mock_services import get_psl_search

    ranked = get_psl_search(category="Cloud Infrastructure", criteria_weights=weights)

    table = Table(title="PSL Ranking", header_style="bold #0F2067")
    table.add_column("Rank")
    table.add_column("Supplier")
    table.add_column("Tier")
    table.add_column("Weighted Score")

    for s in ranked:
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(s["rank"], f"#{s['rank']}")
        table.add_row(medal, s["name"], s.get("tier", ""), f"{s['weighted_score']:.4f}")

    console.print(table)


def main():
    app()


if __name__ == "__main__":
    main()
