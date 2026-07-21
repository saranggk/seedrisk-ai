"""
Tests for Unit U2 (score matches against predict_upset()). See
docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.
"""

from app.models import Match, Player
from app.services.upset_model import predict_upset
from scripts.backtest_calibration.loader import ScoredMatch
from scripts.backtest_calibration.scoring import score_matches


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
    }
    base.update(overrides)
    return Player(**base)


def _scored_match(actual_winner, tour="ATP", **player_overrides):
    match = Match(
        match_id="ATP-2024-540-100",
        round="R128",
        favorite=_player("Favorite", 1, **player_overrides.get("favorite", {})),
        underdog=_player("Underdog", 100, **player_overrides.get("underdog", {})),
    )
    return ScoredMatch(match=match, actual_winner=actual_winner, tour=tour)


def test_favorite_wins_as_predicted():
    scored = _scored_match(actual_winner="favorite")

    results = score_matches([scored])

    prediction = predict_upset(scored.match)
    assert len(results) == 1
    result = results[0]
    assert result["outcome"] == 1
    assert result["favorite_win_probability"] == prediction.favorite_win_probability
    assert result["squared_error"] == (1 - prediction.favorite_win_probability) ** 2


def test_underdog_wins_is_an_upset():
    scored = _scored_match(actual_winner="underdog")

    results = score_matches([scored])

    prediction = predict_upset(scored.match)
    result = results[0]
    assert result["outcome"] == 0
    assert result["squared_error"] == prediction.favorite_win_probability ** 2


def test_result_carries_the_real_models_risk_label():
    scored = _scored_match(actual_winner="favorite")

    results = score_matches([scored])

    prediction = predict_upset(scored.match)
    assert results[0]["risk_label"] == prediction.risk_label
    assert results[0]["match_id"] == scored.match.match_id
    assert results[0]["tour"] == "ATP"
