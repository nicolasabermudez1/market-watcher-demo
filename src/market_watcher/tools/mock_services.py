"""Mock data service tools — wrap fixture files as agent-callable function tools."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from agents import function_tool

from market_watcher.config import FIXTURES_DIR, DEMO_CATEGORY_SUBDIR


def _supplier_dir() -> Path:
    return FIXTURES_DIR / "suppliers" / DEMO_CATEGORY_SUBDIR


def _load_supplier(supplier_id: str) -> dict:
    with open(_supplier_dir() / f"{supplier_id}.json", encoding="utf-8") as f:
        return json.load(f)


def _load_fixture(filename: str) -> Any:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


# ── Plain business-logic functions ──────────────────────────────────────────

def get_supplier_360(supplier_id: str) -> dict:
    try:
        return {"status": "ok", "supplier": _load_supplier(supplier_id.lower())}
    except FileNotFoundError:
        valid = [p.stem for p in _supplier_dir().glob("*.json")]
        return {"status": "error", "message": f"Supplier '{supplier_id}' not found. Valid: {', '.join(valid)}"}


def list_suppliers() -> list[dict]:
    """Return summary cards for all PSL suppliers in the current category."""
    out = []
    for p in sorted(_supplier_dir().glob("*.json")):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        out.append({
            "supplier_id": d["supplier_id"],
            "name": d["name"],
            "subcategory": d.get("subcategory", ""),
            "tier": d.get("tier", ""),
            "status": d.get("status", ""),
            "spend_ytd_gbp": d.get("spend", {}).get("ytd_gbp", 0),
            "contract_expiry": d.get("contract", {}).get("expiry", ""),
            "risk_count": len(d.get("risks", [])),
            "high_risks": sum(1 for r in d.get("risks", []) if r.get("severity") == "High"),
            "dnb_score": d.get("financials", {}).get("dnb_risk_score"),
            "ecovadis": d.get("esg", {}).get("ecovadis_score"),
            "gartner": d.get("gartner", {}).get("quadrant", ""),
        })
    return out


def get_certification_register() -> list[dict]:
    certs = _load_fixture("certifications.json")
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


def get_pestle() -> dict:
    return _load_fixture("pestle.json")


def get_industry_risks() -> list[dict]:
    return _load_fixture("industry_risks.json")


def get_regulations() -> list[dict]:
    return _load_fixture("regulations.json")


def get_contract_pipeline() -> list[dict]:
    return _load_fixture("contract_pipeline.json")


def get_market_intel(limit: int = 10) -> list[dict]:
    items = _load_fixture("market_intel.json")
    return items[:limit]


def get_psl_search(category: str, criteria_weights: dict) -> list[dict]:
    """Rank PSL suppliers by criteria_weights. Generic scoring derived from supplier fixtures."""
    suppliers_raw = []
    for p in sorted(_supplier_dir().glob("*.json")):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)

        # Derive 0-1 scores from fixture data
        fin = d.get("financials", {})
        esg = d.get("esg", {})
        gartner = d.get("gartner", {})
        high_risks = sum(1 for r in d.get("risks", []) if r.get("severity") == "High")

        scores = {
            # Lower D&B risk score => higher safety score (1-best, 5-worst)
            "quality": round(1.0 - (fin.get("dnb_risk_score", 3) - 1) / 4, 2),
            # ESG: Ecovadis 0-100 → 0-1
            "esg": round(esg.get("ecovadis_score", 50) / 100, 2),
            # Price: invert margin (high margin = pricier vendor); cap 0-1
            "price": round(1.0 - min(fin.get("ebitda_margin_pct", 30) / 50, 1.0), 2),
            # Delivery_speed: subcategory-specific heuristic (Microsoft/AWS/Salesforce are fastest)
            "delivery_speed": 0.85,
            # Payment terms: longer terms = better for buyer; parse Net XX
            "payment_terms": _parse_payment_score(d.get("contract", {}).get("payment_terms", "Net 30")),
            # Support: Gartner ATE axis as proxy
            "support": round(gartner.get("ability_to_execute", 3.5) / 5, 2),
        }

        suppliers_raw.append({
            "supplier_id": d["supplier_id"],
            "name": d["name"],
            "subcategory": d.get("subcategory", ""),
            "tier": d.get("tier", "Approved"),
            "scores": scores,
            "contact": f"enterprise@{d['supplier_id']}.com (mock)",
            "risk_count": len(d.get("risks", [])),
            "high_risk_count": high_risks,
        })

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


def _parse_payment_score(terms: str) -> float:
    """Net 30 → 0.5, Net 45 → 0.75, Net 60 → 1.0; consumption-based → 0.4."""
    if "consumption" in terms.lower():
        return 0.4
    digits = "".join(c for c in terms if c.isdigit())
    if not digits:
        return 0.5
    days = int(digits)
    return min(days / 60, 1.0)


def get_news_for_category(category: str, limit: int = 5) -> list[dict]:
    """Return market intel items shaped as news headlines."""
    items = _load_fixture("market_intel.json")
    out = []
    for item in items[:limit]:
        out.append({
            "headline": item["title"],
            "source": item["source"],
            "url": "",
            "summary": item["snippet"],
            "date": item["date"],
            "tag": item.get("tag", "news"),
        })
    return out


# ── @function_tool wrappers ──────────────────────────────────────────────────

@function_tool
def mock_supplier_360(supplier_id: str) -> dict:
    """Return a 360 profile (financials, certifications, spend, news, risks) for one supplier."""
    return get_supplier_360(supplier_id)


@function_tool
def mock_supplier_directory() -> list[dict]:
    """Return summary cards for all PSL suppliers in the current category."""
    return list_suppliers()


@function_tool
def mock_certification_register() -> list[dict]:
    """Return all supplier certifications with expiry dates and status flags."""
    return get_certification_register()


@function_tool
def mock_pestle() -> dict:
    """Return the PESTLE analysis for the current category."""
    return get_pestle()


@function_tool
def mock_industry_risks() -> list[dict]:
    """Return the industry-level risk register for the current category."""
    return get_industry_risks()


@function_tool
def mock_regulations() -> list[dict]:
    """Return the regulatory landscape affecting the current category."""
    return get_regulations()


@function_tool
def mock_contract_pipeline() -> list[dict]:
    """Return the upcoming contract renewal pipeline."""
    return get_contract_pipeline()


@function_tool
def mock_market_intel(limit: int = 10) -> list[dict]:
    """Return recent market intelligence (Gartner / Forrester / news / internal)."""
    return get_market_intel(limit)


@function_tool(strict_mode=False)
def mock_psl_search(
    category: str,
    price: float = 0.20,
    quality: float = 0.25,
    esg: float = 0.15,
    delivery_speed: float = 0.10,
    payment_terms: float = 0.10,
    support: float = 0.20,
) -> list[dict]:
    """Return ranked PSL suppliers re-weighted by the given criteria scores (0-1)."""
    weights = {"price": price, "quality": quality, "esg": esg,
               "delivery_speed": delivery_speed, "payment_terms": payment_terms, "support": support}
    return get_psl_search(category, weights)


@function_tool
def mock_news_for_category(category: str, limit: int = 5) -> list[dict]:
    """Return curated market news items for the category."""
    return get_news_for_category(category, limit)
