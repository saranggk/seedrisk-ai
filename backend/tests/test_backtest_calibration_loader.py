"""
Tests for Unit U1 (load and filter backtest matches for scoring). See
docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.
"""

import json

from scripts.backtest_calibration.loader import filter_scoreable, load_records
from tests._backtest_calibration_fixtures import player_dict as _player


def _record(favorite=None, underdog=None, **overrides):
    base = {
        "match_id": "ATP-2024-540-100",
        "date": "2024-07-01",
        "tour": "ATP",
        "round": "R128",
        "actual_winner": "favorite",
        "favorite": favorite or _player("Favorite", ranking=1),
        "underdog": underdog or _player("Underdog", ranking=100),
    }
    base.update(overrides)
    return base


def test_included_match_produces_valid_match():
    scored, excluded_count = filter_scoreable([_record()])

    assert excluded_count == 0
    assert len(scored) == 1
    assert scored[0].match.favorite.player_name == "Favorite"
    assert scored[0].match.underdog.player_name == "Underdog"
    assert scored[0].actual_winner == "favorite"
    assert scored[0].tour == "ATP"


def test_excluded_missing_surface_win_pct():
    record = _record(favorite=_player("Favorite", ranking=1, surface_win_pct=None))

    scored, excluded_count = filter_scoreable([record])

    assert scored == []
    assert excluded_count == 1


def test_excluded_missing_tournament_win_pct():
    record = _record(underdog=_player("Underdog", ranking=100, tournament_win_pct=None))

    scored, excluded_count = filter_scoreable([record])

    assert scored == []
    assert excluded_count == 1


def test_excluded_null_ranking():
    record = _record(favorite=_player("Favorite", ranking=None))

    scored, excluded_count = filter_scoreable([record])

    assert scored == []
    assert excluded_count == 1


def test_excluded_nan_field():
    """Regression: the real dataset encodes some missing grass rates as NaN,
    not null (see KTD3). A NaN must be excluded, not passed to Player()."""
    record = _record(favorite=_player("Favorite", ranking=1, surface_hold_rate=float("nan")))

    scored, excluded_count = filter_scoreable([record])

    assert scored == []
    assert excluded_count == 1


def test_counts_sum_to_total():
    records = [
        _record(match_id="A"),
        _record(match_id="B", favorite=_player("F2", ranking=1, tiebreak_win_pct=None)),
        _record(match_id="C", underdog=_player("U2", ranking=50, surface_break_rate=float("nan"))),
    ]

    scored, excluded_count = filter_scoreable(records)

    assert len(scored) + excluded_count == len(records)
    assert len(scored) == 1
    assert excluded_count == 2


def test_extra_field_thin_grass_history_does_not_crash():
    """Player has no thin_grass_history field; extra keys must be ignored,
    not raise a pydantic validation error (KTD3)."""
    record = _record()

    scored, _ = filter_scoreable([record])

    assert len(scored) == 1


def test_excluded_missing_h2h_wins():
    """Regression (code review, correctness + adversarial corroborated):
    Player requires player_name/last_10_record/h2h_wins/h2h_losses too, not
    just the 7 rate fields -- a missing value there must exclude the match,
    not reach Player(**dict) uncaught and crash the whole run."""
    record = _record(favorite=_player("Favorite", ranking=1, h2h_wins=None))

    scored, excluded_count = filter_scoreable([record])

    assert scored == []
    assert excluded_count == 1


def test_load_records_reads_json_file(tmp_path):
    records = [_record(match_id="A"), _record(match_id="B")]
    path = tmp_path / "matches.json"
    path.write_text(json.dumps(records))

    loaded = load_records(path)

    assert loaded == records
