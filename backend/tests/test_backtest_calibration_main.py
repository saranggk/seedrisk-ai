"""
Tests for Unit U4 (orchestrate, write the committed report). See
docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.
"""

import json

from scripts.backtest_calibration import main as main_module
from scripts.backtest_calibration.main import build_report, write_report
from tests._backtest_calibration_fixtures import player_dict as _player


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


def test_main_runs_end_to_end_and_writes_report(tmp_path, monkeypatch, capsys):
    records = [_record("A"), _record("B", tour="WTA", actual_winner="underdog")]
    data_file = tmp_path / "matches.json"
    data_file.write_text(json.dumps(records))
    output_file = tmp_path / "calibration_report.json"
    monkeypatch.setattr(main_module, "DATA_FILE", data_file)
    monkeypatch.setattr(main_module, "OUTPUT_FILE", output_file)

    main_module.main()

    with open(output_file, encoding="utf-8") as f:
        report = json.load(f)
    assert report["total_count"] == 2
    assert "Overall Brier score" in capsys.readouterr().out


def test_main_handles_all_excluded_dataset_without_crashing(tmp_path, monkeypatch, capsys):
    """Regression (code review, adversarial, confidence 100): brier_score is
    None when nothing is scoreable, and the summary print used to format it
    with :.4f unconditionally, raising TypeError instead of writing the
    report and exiting cleanly."""
    excluded_favorite = _player("F", 1, surface_win_pct=None)
    records = [_record("A", favorite=excluded_favorite)]
    data_file = tmp_path / "matches.json"
    data_file.write_text(json.dumps(records))
    output_file = tmp_path / "calibration_report.json"
    monkeypatch.setattr(main_module, "DATA_FILE", data_file)
    monkeypatch.setattr(main_module, "OUTPUT_FILE", output_file)

    main_module.main()  # must not raise

    with open(output_file, encoding="utf-8") as f:
        report = json.load(f)
    assert report["scored_count"] == 0
    assert report["brier_score"] is None
    assert "No scoreable matches" in capsys.readouterr().out
