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


def test_reliability_bins_collapse_to_one_bin_when_all_probabilities_match():
    """Edge case: when every result's probability already sits on a
    BIN_WIDTH-aligned value, floor(min) == ceil(max) and _bin_edges' hi==lo
    branch must widen the range instead of producing a zero-width bin."""
    results = [
        _result("A", "ATP", "Low", 0.60, 1),
        _result("B", "ATP", "Low", 0.60, 0),
    ]

    metrics = compute_metrics(results)

    assert len(metrics["reliability_bins"]) == 1
    only_bin = metrics["reliability_bins"][0]
    assert only_bin["bin_low"] == 0.60
    assert only_bin["bin_high"] == 0.65
    assert only_bin["count"] == 2


def test_reliability_bin_index_places_the_max_value_in_the_last_bin():
    """Edge case: a probability exactly equal to the computed max edge falls
    outside every half-open [low, high) bin and must land in the final bin
    via _bin_index's fallback, not be dropped or misplaced."""
    results = [_result("A", "ATP", "High", 0.95, 0)]

    metrics = compute_metrics(results)

    bins = metrics["reliability_bins"]
    assert sum(b["count"] for b in bins) == 1
    assert bins[-1]["count"] == 1


def test_tour_breakdown_raises_on_unrecognized_tour():
    """Fail loud, not silent (code review finding): a tour outside
    {"ATP", "WTA"} must not silently vanish from by_tour while still
    counting toward the top-level scored_count."""
    results = [_result("A", "ITF", "Low", 0.9, 1)]

    with pytest.raises(ValueError, match="ITF"):
        compute_metrics(results)


def test_risk_label_breakdown_raises_on_unrecognized_label():
    """Fail loud, not silent (code review finding): a risk_label outside the
    four upset_model.py can produce must not silently vanish."""
    results = [_result("A", "ATP", "Unknown", 0.9, 1)]

    with pytest.raises(ValueError, match="Unknown"):
        compute_metrics(results)
