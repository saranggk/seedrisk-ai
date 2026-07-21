"""
Tests for Unit U1 (load and filter backtest matches for scoring). See
docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.
"""

import math

from scripts.backtest_calibration.loader import filter_scoreable

REQUIRED_FIELDS = (
    "ranking", "surface_win_pct", "recent_win_pct", "tournament_win_pct",
    "surface_hold_rate", "surface_break_rate", "tiebreak_win_pct",
)


def _player(name="Player", **overrides):
    base = {
        "player_name": name,
        "ranking": 10,
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
