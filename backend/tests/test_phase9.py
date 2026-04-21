from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.services.calibration import get_latest_calibration_report

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_golden_set_fixture_contains_balanced_labels() -> None:
    fixture = json.loads((FIXTURE_DIR / "golden_set.json").read_text(encoding="utf-8"))
    expected_verdicts = [
        str(item.get("metadata_json", {}).get("expected_verdict", ""))
        for item in fixture["items"]
    ]

    assert len(fixture["items"]) >= 10
    assert expected_verdicts.count("pass") >= 5
    assert expected_verdicts.count("fail") >= 5


def test_calibration_service_computes_fixture_backed_metrics() -> None:
    report = get_latest_calibration_report()

    assert report.fixture_id == "golden_set_support_faq_v1"
    assert report.scorer_config_id == "sc_keyword_overlap_v1"
    assert report.total_cases == 12
    assert report.labelled_pass_cases == 5
    assert report.labelled_fail_cases == 7
    assert report.true_positive_count == 5
    assert report.false_positive_count == 0
    assert report.true_negative_count == 7
    assert report.false_negative_count == 0
    assert report.precision == 1.0
    assert report.recall == 1.0
    assert report.accuracy == 1.0
    assert any(row.category == "refund_policy" for row in report.per_category)
    assert report.disagreements == []


def test_latest_calibration_endpoint_returns_report(client: TestClient) -> None:
    response = client.get("/api/v1/calibration/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["fixture_id"] == "golden_set_support_faq_v1"
    assert body["scorer_config_id"] == "sc_keyword_overlap_v1"
    assert body["precision"] == 1.0
    assert body["recall"] == 1.0
    assert body["accuracy"] == 1.0
    assert body["true_positive_count"] == 5
    assert body["true_negative_count"] == 7
    assert body["false_positive_count"] == 0
    assert body["false_negative_count"] == 0
    assert any(row["category"] == "policy_lookup" for row in body["per_category"])
