"""
Tests for Unit U4 (orchestrate, write the committed report). See
docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.
"""

import json

from scripts.backtest_calibration.main import build_report, write_report


def _player(name, ranking, **overrides):
    base = {
        "player_name": name,
        "ranking": ranking,
        "seed": None,
        "surface_win_pct": 0.6,
        "recent_win_pct": 0.5,
        "tournament_win_pct": 0.5,
        "surface_hold_rate": 0.8,
        "surface_break_rate": 0.2,
        "tiebreak_win_pct": 0.5,
        "last_10_record": "5-5",
        "h2h_wins": 0,
        "h2h_losses": 0,
        "thin_grass_history": False,
    }
    base.update(overrides)
    return base


def _record(match_id, favorite=None, underdog=None, tour="ATP", actual_winner="favorite"):
    return {
        "match_id": match_id,
        "date": "2024-07-01",
        "tour": tour,
        "round": "R128",
        "actual_winner": actual_winner,
        "favorite": favorite or _player("Favorite", 1),
        "underdog": underdog or _player("Underdog", 100),
    }


def test_build_report_counts_are_internally_consistent():
    records = [
        _record("A"),
        _record("B", favorite=_player("F2", 1, surface_win_pct=None)),  # excluded
        _record("C", tour="WTA", actual_winner="underdog"),
    ]

    report = build_report(records)

    assert report["total_count"] == 3
    assert report["scored_count"] == 2
    assert report["excluded_count"] == 1
    assert report["scored_count"] + report["excluded_count"] == report["total_count"]
    assert "brier_score" in report
    assert "reliability_bins" in report
    assert "by_tour" in report
    assert "by_risk_label" in report


def test_write_report_produces_valid_json_file(tmp_path):
    report = {"total_count": 1, "scored_count": 1, "excluded_count": 0}
    output_file = tmp_path / "calibration_report.json"

    write_report(report, output_file)

    with open(output_file, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == report
