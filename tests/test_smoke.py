"""Smoke tests — validates fixtures, tools, and basic agent wiring."""

import json
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_fixtures_exist():
    fixtures = REPO_ROOT / "data" / "fixtures"
    for f in [
        "certifications.json", "pestle.json", "industry_risks.json",
        "regulations.json", "contract_pipeline.json", "market_intel.json",
        "spend_by_subcategory.csv",
    ]:
        assert (fixtures / f).exists(), f"Missing fixture: {f}"
    for vendor in ["microsoft", "sap", "oracle", "salesforce", "servicenow",
                   "workday", "atlassian", "pega", "snowflake"]:
        p = fixtures / "suppliers" / "it_software" / f"{vendor}.json"
        assert p.exists(), f"Missing vendor fixture: {vendor}"


def test_vendor_fixtures_valid():
    fixtures = REPO_ROOT / "data" / "fixtures" / "suppliers" / "it_software"
    for p in fixtures.glob("*.json"):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        for key in ["supplier_id", "name", "subcategory", "tier", "financials",
                    "contract", "certifications", "risks", "esg", "gartner"]:
            assert key in d, f"{p.stem} missing key {key}"


def test_pestle_valid():
    with open(REPO_ROOT / "data" / "fixtures" / "pestle.json", encoding="utf-8") as f:
        p = json.load(f)
    assert "factors" in p
    assert len(p["factors"]) == 6


def test_industry_risks_valid():
    with open(REPO_ROOT / "data" / "fixtures" / "industry_risks.json", encoding="utf-8") as f:
        risks = json.load(f)
    assert len(risks) >= 5
    for r in risks:
        assert r["severity"] in ("High", "Medium", "Low")


def test_regulations_valid():
    with open(REPO_ROOT / "data" / "fixtures" / "regulations.json", encoding="utf-8") as f:
        regs = json.load(f)
    assert len(regs) >= 4


def test_supplier_360_tool():
    from market_watcher.tools.mock_services import get_supplier_360
    r = get_supplier_360("microsoft")
    assert r["status"] == "ok"
    assert r["supplier"]["name"] == "Microsoft Corporation"

    r2 = get_supplier_360("nonexistent")
    assert r2["status"] == "error"


def test_list_suppliers_returns_all():
    from market_watcher.tools.mock_services import list_suppliers
    suppliers = list_suppliers()
    assert len(suppliers) == 9  # 9 IT software vendors
    names = {s["supplier_id"] for s in suppliers}
    for v in ["microsoft", "sap", "oracle", "salesforce", "servicenow",
              "workday", "atlassian", "pega", "snowflake"]:
        assert v in names


def test_psl_ranking_esg_weight():
    from market_watcher.tools.mock_services import get_psl_search
    # Heavy ESG weight should put Salesforce (Ecovadis 86) at the top.
    ranked = get_psl_search("IT Software",
                            {"price": 0, "quality": 0, "esg": 1.0,
                             "delivery_speed": 0, "payment_terms": 0, "support": 0})
    assert ranked[0]["supplier_id"] == "salesforce"


def test_certification_register():
    from market_watcher.tools.mock_services import get_certification_register
    certs = get_certification_register()
    assert len(certs) >= 5
    for c in certs:
        assert c["status"] in ("Valid", "Expiring Soon", "Expired")


def test_pestle_tool():
    from market_watcher.tools.mock_services import get_pestle
    p = get_pestle()
    dims = {f["dimension"] for f in p["factors"]}
    assert dims == {"Political", "Economic", "Social", "Technological", "Legal", "Environmental"}


def test_industry_risks_tool():
    from market_watcher.tools.mock_services import get_industry_risks
    risks = get_industry_risks()
    high = [r for r in risks if r["severity"] == "High"]
    assert len(high) >= 2


def test_regulations_tool():
    from market_watcher.tools.mock_services import get_regulations
    regs = get_regulations()
    titles = [r["regulation"] for r in regs]
    assert any("AI Act" in t for t in titles)


def test_contract_pipeline_tool():
    from market_watcher.tools.mock_services import get_contract_pipeline
    pipeline = get_contract_pipeline()
    assert len(pipeline) >= 5
    for c in pipeline:
        assert c["priority"] in ("Critical", "High", "Medium", "Low")


def test_category_strategy_tool():
    from market_watcher.tools.mock_services import get_category_strategy
    s = get_category_strategy()
    assert "porters" in s
    assert "swot" in s
    assert "kraljic" in s
    assert "sourcing_strategy" in s
    assert "objectives" in s
    assert len(s["porters"]["forces"]) == 5
    assert len(s["kraljic"]["quadrants"]) == 4


def test_market_intel_tool():
    from market_watcher.tools.mock_services import get_market_intel
    items = get_market_intel(limit=5)
    assert len(items) == 5
    tags = {item.get("tag") for item in items}
    assert "analyst" in tags or "news" in tags


def test_draft_cert_chase_email_english():
    from market_watcher.tools.document_gen import _draft_cert_chase_email
    body = _draft_cert_chase_email("SAP SE", "Cyber Essentials Plus", "SAP-CYBERESS",
                                    "2026-04-15", -26, "english")
    assert "SAP" in body
    assert "Cyber Essentials Plus" in body


def test_draft_cert_chase_email_spanish():
    from market_watcher.tools.document_gen import _draft_cert_chase_email
    body = _draft_cert_chase_email("Oracle Corporation", "ISO 9001", "ORCL-ISO9001",
                                    "2025-11-01", -192, "spanish")
    assert "Oracle" in body


def test_outputs_dir_writable():
    from market_watcher.config import OUTPUTS_DIR
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    p = OUTPUTS_DIR / ".smoke_test"
    p.write_text("ok"); assert p.exists(); p.unlink()


def test_generate_weekly_digest():
    from market_watcher.tools.document_gen import _generate_weekly_digest
    risks = [{"supplier": "SAP", "type": "Migration", "description": "ECC EoL 2027", "severity": "High"}]
    news = [{"headline": "Test", "source": "Gartner", "url": "", "summary": "summary"}]
    p = _generate_weekly_digest("IT Software", risks, news, run_date="2026-05-11-test")
    assert Path(p).exists() and p.endswith(".docx")
    Path(p).unlink()


def test_agents_build():
    """Verify both agents build with the new tool set."""
    import os
    os.environ.setdefault("GEMINI_API_KEY", "dummy-for-import-test")
    from market_watcher.subagents.batch import build_batch_agent
    from market_watcher.subagents.query import build_query_agent
    ba = build_batch_agent()
    qa = build_query_agent()
    assert ba.name == "MarketWatcherBatchAgent"
    assert qa.name == "MarketWatcherQueryAgent"
    assert len(ba.tools) >= 8
    assert len(qa.tools) >= 4
