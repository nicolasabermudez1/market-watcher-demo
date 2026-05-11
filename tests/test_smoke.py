"""Smoke tests — validates fixtures, tools, and basic agent wiring."""

import json
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_fixtures_exist():
    fixtures = REPO_ROOT / "data" / "fixtures"
    assert (fixtures / "certifications.json").exists(), "certifications.json missing"
    assert (fixtures / "spend_by_category.csv").exists(), "spend CSV missing"
    assert (fixtures / "mock_news_seed.json").exists(), "news seed missing"
    assert (fixtures / "category_strategy.md").exists(), "category strategy missing"
    for sup in ["microsoft", "aws", "gcp"]:
        p = fixtures / "suppliers" / "cloud_infrastructure" / f"{sup}.json"
        assert p.exists(), f"Supplier fixture missing: {sup}"


def test_supplier_fixtures_valid():
    fixtures = REPO_ROOT / "data" / "fixtures"
    for sup in ["microsoft", "aws", "gcp"]:
        with open(fixtures / "suppliers" / "cloud_infrastructure" / f"{sup}.json") as f:
            data = json.load(f)
        assert "supplier_id" in data
        assert "name" in data
        assert "certifications" in data
        assert "financials" in data
        assert "risks" in data


def test_certifications_fixture_valid():
    with open(REPO_ROOT / "data" / "fixtures" / "certifications.json") as f:
        certs = json.load(f)
    assert len(certs) >= 5
    for cert in certs:
        assert "cert_id" in cert
        assert "supplier_id" in cert
        assert "expiry" in cert
        date.fromisoformat(cert["expiry"])


def test_news_seed_valid():
    with open(REPO_ROOT / "data" / "fixtures" / "mock_news_seed.json") as f:
        news = json.load(f)
    assert len(news) >= 10
    for item in news:
        assert "headline" in item
        assert "summary" in item
        assert "risk_signal" in item


def test_supplier_360():
    from market_watcher.tools.mock_services import get_supplier_360
    result = get_supplier_360("microsoft")
    assert result["status"] == "ok"
    assert result["supplier"]["name"] == "Microsoft Corporation"


def test_supplier_360_invalid():
    from market_watcher.tools.mock_services import get_supplier_360
    result = get_supplier_360("nonexistent")
    assert result["status"] == "error"


def test_certification_register():
    from market_watcher.tools.mock_services import get_certification_register
    certs = get_certification_register()
    assert len(certs) >= 5
    for cert in certs:
        assert "status" in cert
        assert "days_to_expiry" in cert


def test_psl_search_ranking_price_heavy():
    from market_watcher.tools.mock_services import get_psl_search
    # Price-heavy weighting — GCP has highest price score (0.72)
    ranked = get_psl_search(
        category="Cloud Infrastructure",
        criteria_weights={"price": 1.0, "quality": 0.0, "esg": 0.0,
                          "delivery_speed": 0.0, "payment_terms": 0.0, "support": 0.0},
    )
    assert len(ranked) == 3
    assert ranked[0]["rank"] == 1
    assert ranked[0]["supplier_id"] == "gcp"


def test_psl_search_esg_weighting():
    from market_watcher.tools.mock_services import get_psl_search
    # ESG-heavy — GCP has highest ESG score (0.95)
    ranked = get_psl_search(
        category="Cloud Infrastructure",
        criteria_weights={"price": 0.0, "quality": 0.0, "esg": 1.0,
                          "delivery_speed": 0.0, "payment_terms": 0.0, "support": 0.0},
    )
    assert ranked[0]["supplier_id"] == "gcp"


def test_draft_cert_chase_email_english():
    from market_watcher.tools.document_gen import _draft_cert_chase_email
    body = _draft_cert_chase_email(
        supplier_name="Amazon Web Services",
        cert_type="ISO 9001",
        cert_id="AWS-ISO9001",
        expiry_date="2024-11-14",
        days_to_expiry=-176,
        language="english",
    )
    assert "AWS-ISO9001" in body
    assert "Amazon Web Services" in body
    assert "ISO 9001" in body


def test_draft_cert_chase_email_spanish():
    from market_watcher.tools.document_gen import _draft_cert_chase_email
    body = _draft_cert_chase_email(
        supplier_name="Google Cloud Platform",
        cert_type="ISO 14001",
        cert_id="GCP-ISO14001",
        expiry_date="2025-07-31",
        days_to_expiry=83,
        language="spanish",
    )
    assert "GCP-ISO14001" in body
    assert "ISO 14001" in body


def test_outputs_dir_writable():
    from market_watcher.config import OUTPUTS_DIR
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    test_file = OUTPUTS_DIR / ".smoke_test"
    test_file.write_text("ok")
    assert test_file.exists()
    test_file.unlink()


def test_runs_dir_writable():
    from market_watcher.config import RUNS_DIR
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    test_file = RUNS_DIR / ".smoke_test"
    test_file.write_text("ok")
    assert test_file.exists()
    test_file.unlink()


def test_generate_weekly_digest():
    from market_watcher.tools.document_gen import _generate_weekly_digest
    risks = [
        {"supplier": "AWS", "type": "Contract", "description": "Renewal pending", "severity": "High"},
        {"supplier": "Microsoft", "type": "Concentration", "description": "44% spend share", "severity": "Medium"},
    ]
    news = [
        {"headline": "Test news", "source": "FT", "url": "https://example.com", "summary": "A short summary."},
    ]
    path = _generate_weekly_digest("Cloud Infrastructure", risks, news, run_date="2026-05-09-test")
    assert Path(path).exists()
    assert path.endswith(".docx")
    Path(path).unlink()  # cleanup
