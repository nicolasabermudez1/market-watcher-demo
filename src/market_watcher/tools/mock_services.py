"""Mock data service tools — wrap fixture files as agent-callable function tools."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from agents import function_tool

from market_watcher.config import FIXTURES_DIR


def _load_supplier(supplier_id: str) -> dict:
    path = FIXTURES_DIR / "suppliers" / "cloud_infrastructure" / f"{supplier_id}.json"
    with open(path) as f:
        return json.load(f)


def _load_certifications() -> list[dict]:
    with open(FIXTURES_DIR / "certifications.json") as f:
        return json.load(f)


def _load_news_seed() -> list[dict]:
    with open(FIXTURES_DIR / "mock_news_seed.json") as f:
        return json.load(f)


# ── Plain business-logic functions (used directly by tests and UI) ──────────

def get_supplier_360(supplier_id: str) -> dict:
    try:
        data = _load_supplier(supplier_id.lower())
        return {"status": "ok", "supplier": data}
    except FileNotFoundError:
        return {"status": "error", "message": f"Supplier '{supplier_id}' not found. Valid: microsoft, aws, gcp"}


def get_certification_register() -> list[dict]:
    certs = _load_certifications()
    today = date.today()
    for cert in certs:
        exp = date.fromisoformat(cert["expiry"])
        cert["days_to_expiry"] = (exp - today).days
        cert["status"] = (
            "Expired" if cert["days_to_expiry"] < 0
            else "Expiring Soon" if cert["days_to_expiry"] <= 90
            else "Valid"
        )
    return certs


def get_psl_search(category: str, criteria_weights: dict) -> list[dict]:
    """Rank PSL suppliers by criteria_weights (keys: price, quality, esg, delivery_speed, payment_terms, support)."""
    suppliers_raw = [
        {
            "supplier_id": "microsoft",
            "name": "Microsoft Corporation",
            "scores": {"price": 0.55, "quality": 0.95, "esg": 0.90, "delivery_speed": 0.85, "payment_terms": 0.70, "support": 0.95},
            "tier": "Preferred",
            "contact": "enterprise@microsoft.com (mock)",
            "lead_time_days": 1,
            "min_order_gbp": 0,
        },
        {
            "supplier_id": "aws",
            "name": "Amazon Web Services",
            "scores": {"price": 0.60, "quality": 0.92, "esg": 0.65, "delivery_speed": 0.90, "payment_terms": 0.60, "support": 0.88},
            "tier": "Preferred",
            "contact": "enterprise@aws.com (mock)",
            "lead_time_days": 1,
            "min_order_gbp": 0,
        },
        {
            "supplier_id": "gcp",
            "name": "Google Cloud Platform",
            "scores": {"price": 0.72, "quality": 0.88, "esg": 0.95, "delivery_speed": 0.88, "payment_terms": 0.75, "support": 0.80},
            "tier": "Approved",
            "contact": "cloud-sales@google.com (mock)",
            "lead_time_days": 1,
            "min_order_gbp": 0,
        },
    ]

    keys = ["price", "quality", "esg", "delivery_speed", "payment_terms", "support"]
    weights = {k: float(criteria_weights.get(k, 0.0)) for k in keys}
    total = sum(weights.values()) or 1.0
    weights = {k: v / total for k, v in weights.items()}

    for s in suppliers_raw:
        s["weighted_score"] = round(sum(s["scores"][k] * weights[k] for k in keys), 4)

    ranked = sorted(suppliers_raw, key=lambda x: x["weighted_score"], reverse=True)
    for i, s in enumerate(ranked):
        s["rank"] = i + 1
    return ranked


def get_news_for_category(category: str, limit: int = 5) -> list[dict]:
    return _load_news_seed()[:limit]


# ── @function_tool wrappers (used by agents) ─────────────────────────────────

@function_tool
def mock_supplier_360(supplier_id: str) -> dict:
    """Return a merged 360-degree supplier profile including financials, certifications, spend, and news.
    Valid supplier_ids: microsoft, aws, gcp.
    """
    return get_supplier_360(supplier_id)


@function_tool
def mock_certification_register() -> list[dict]:
    """Return all supplier certifications with expiry dates and status flags."""
    return get_certification_register()


@function_tool(strict_mode=False)
def mock_psl_search(
    category: str,
    price: float = 0.25,
    quality: float = 0.30,
    esg: float = 0.15,
    delivery_speed: float = 0.15,
    payment_terms: float = 0.05,
    support: float = 0.10,
) -> list[dict]:
    """Return ranked PSL suppliers for a category, re-ranked by criteria weights.
    Each weight is a float 0-1 (will be normalised to sum to 1).
    Use higher values for criteria the user cares more about.
    """
    weights = {
        "price": price, "quality": quality, "esg": esg,
        "delivery_speed": delivery_speed, "payment_terms": payment_terms, "support": support,
    }
    return get_psl_search(category, weights)


@function_tool
def mock_news_for_category(category: str, limit: int = 5) -> list[dict]:
    """Return mock news seed items for the given category (fallback when web search unavailable)."""
    return get_news_for_category(category, limit)
