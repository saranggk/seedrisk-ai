"""
Coverage for GET /calibration -- confirms the endpoint exposes exactly the
committed report's overall reliability_bins and nothing else (R1-R3 of
docs/plans/2026-07-23-004-feat-calibration-aware-confidence-display-plan.md).
"""

import json

from fastapi.testclient import TestClient

from app.data.loader import CALIBRATION_FILE
from app.main import app

client = TestClient(app)

EXPECTED_BIN_FIELDS = {
    "bin_low",
    "bin_high",
    "count",
    "mean_predicted_probability",
    "observed_favorite_win_rate",
}


def _committed_report() -> dict:
    with open(CALIBRATION_FILE, encoding="utf-8") as f:
        return json.load(f)


def test_returns_the_committed_reports_overall_reliability_bins():
    response = client.get("/calibration")
    assert response.status_code == 200

    body = response.json()
    expected_bins = _committed_report()["reliability_bins"]

    assert body["reliability_bins"] == expected_bins
    assert len(body["reliability_bins"]) > 0


def test_each_bin_has_exactly_the_expected_fields():
    response = client.get("/calibration")
    for bin_ in response.json()["reliability_bins"]:
        assert set(bin_.keys()) == EXPECTED_BIN_FIELDS


def test_no_other_report_fields_are_exposed():
    response = client.get("/calibration")
    body = response.json()

    assert set(body.keys()) == {"reliability_bins"}
    for leaked_field in ("brier_score", "by_tour", "by_risk_label", "scored_count", "total_count", "excluded_count"):
        assert leaked_field not in body
