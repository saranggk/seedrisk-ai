"""
Tests for Unit U3 (compute calibration metrics). See
docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.
"""

import pytest

from scripts.backtest_calibration.metrics import compute_metrics


def _result(match_id, tour, risk_label, favorite_win_probability, outcome):
    return {
        "match_id": match_id,
        "tour": tour,
        "risk_label": risk_label,
        "favorite_win_probability": favorite_win_probability,
        "outcome": outcome,
        "squared_error": (favorite_win_probability - outcome) ** 2,
    }


def test_overall_brier_score_hand_computed():
    results = [
        _result("A", "ATP", "Low", 0.9, 1),   # (0.9-1)^2 = 0.01
        _result("B", "ATP", "Medium", 0.6, 0),  # (0.6-0)^2 = 0.36
    ]

    metrics = compute_metrics(results)

    assert metrics["brier_score"] == pytest.approx((0.01 + 0.36) / 2)


def test_risk_label_with_zero_matches_reports_null_and_zero_count():
    results = [_result("A", "ATP", "Low", 0.9, 1)]

    metrics = compute_metrics(results)

    assert metrics["by_risk_label"]["Trap Match"]["count"] == 0
    assert metrics["by_risk_label"]["Trap Match"]["observed_upset_rate"] is None


def test_reliability_bin_with_zero_matches_reports_null_rate():
    # Spans 0.35-0.95 with nothing landing in the 0.60-0.65 bin.
    results = [
        _result("A", "ATP", "Low", 0.38, 1),
        _result("B", "ATP", "High", 0.93, 0),
    ]

    metrics = compute_metrics(results)

    empty_bins = [b for b in metrics["reliability_bins"] if b["bin_low"] == 0.60]
    assert len(empty_bins) == 1
    assert empty_bins[0]["count"] == 0
    assert empty_bins[0]["observed_favorite_win_rate"] is None


def test_by_tour_independent_brier_scores():
    results = [
        _result("A", "ATP", "Low", 0.9, 1),     # ATP: 0.01
        _result("B", "ATP", "Low", 0.8, 1),     # ATP: 0.04
        _result("C", "WTA", "Medium", 0.5, 0),  # WTA: 0.25
    ]

    metrics = compute_metrics(results)

    assert metrics["by_tour"]["ATP"]["count"] == 2
    assert metrics["by_tour"]["ATP"]["brier_score"] == pytest.approx((0.01 + 0.04) / 2)
    assert metrics["by_tour"]["WTA"]["count"] == 1
    assert metrics["by_tour"]["WTA"]["brier_score"] == pytest.approx(0.25)


def test_risk_label_breakdown_computed_only_from_given_results():
    """AE2: excluded matches never appear in `results`, so the Trap Match
    bucket's rate reflects only what was actually scored and passed in."""
    results = [
        _result("A", "ATP", "Trap Match", 0.7, 0),  # upset
        _result("B", "ATP", "Trap Match", 0.72, 1),  # not an upset
        _result("C", "WTA", "Low", 0.9, 1),
    ]

    metrics = compute_metrics(results)

    trap = metrics["by_risk_label"]["Trap Match"]
    assert trap["count"] == 2
    assert trap["observed_upset_rate"] == 0.5
