"""
Tests for Unit U2 (score matches against predict_upset()). See
docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.
"""

from app.models import Match, Player
from app.services.upset_model import predict_upset
from scripts.backtest_calibration.loader import ScoredMatch
from scripts.backtest_calibration.scoring import score_matches
from tests._backtest_calibration_fixtures import player_dict


def _player(name, ranking, **overrides):
    # Player ignores the extra thin_grass_history key from player_dict()
    # (pydantic's default extra="ignore" -- see loader.py KTD3).
    return Player(**player_dict(name, ranking, **overrides))


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
