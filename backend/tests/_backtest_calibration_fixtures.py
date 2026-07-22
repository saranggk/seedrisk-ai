"""
Shared player-dict builder for the backtest calibration harness tests.

Extracted here (mirroring _snapshot.py's pattern) after code review found the
per-test-file copy had already drifted once -- the scoring test's copy
silently omitted thin_grass_history.
"""


def player_dict(name="Player", ranking=10, **overrides):
    """A full backtest-record player dict, in the shape
    data/wimbledon_backtest_matches.json actually stores (see
    scripts/backtest_calibration/loader.py's REQUIRED_PLAYER_FIELDS)."""
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
