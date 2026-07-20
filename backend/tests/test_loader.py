"""
Tests for deriving favorite/underdog from ranking (seed as tiebreak) instead
of trusting a stored dataset label. See docs/plans/2026-07-19-001-refactor-
regression-tests-and-surface-schema-plan.md, Unit U3.
"""

import json

from app.data.loader import DATA_FILE, _derive_favorite_underdog, load_matches_raw
from app.models import Match
from app.services.upset_model import predict_upset


def test_derivation_matches_hand_labels_for_all_real_matches():
    """
    For all 16 real matches, ranking-based derivation must exactly agree
    with today's hand-picked favorite/underdog labels (verified during
    brainstorming: every existing match already has favorite.ranking <
    underdog.ranking).
    """
    with open(DATA_FILE, encoding="utf-8") as f:
        raw_matches = json.load(f)

    for match in raw_matches:
        favorite, underdog = _derive_favorite_underdog(
            match["favorite"], match["underdog"]
        )
        assert favorite["player_name"] == match["favorite"]["player_name"], (
            f"{match['match_id']}: derived favorite does not match the stored label"
        )
        assert underdog["player_name"] == match["underdog"]["player_name"], (
            f"{match['match_id']}: derived underdog does not match the stored label"
        )


def test_lower_ranking_wins_regardless_of_input_order():
    better_ranked = {"player_name": "A", "ranking": 5, "seed": 5}
    worse_ranked = {"player_name": "B", "ranking": 50, "seed": None}

    favorite, underdog = _derive_favorite_underdog(worse_ranked, better_ranked)
    assert favorite["player_name"] == "A"
    assert underdog["player_name"] == "B"


def test_equal_ranking_lower_seed_wins():
    player_a = {"player_name": "A", "ranking": 10, "seed": 8}
    player_b = {"player_name": "B", "ranking": 10, "seed": 3}

    favorite, underdog = _derive_favorite_underdog(player_a, player_b)
    assert favorite["player_name"] == "B"  # lower seed (3 < 8) wins
    assert underdog["player_name"] == "A"


def test_equal_ranking_seeded_player_beats_unseeded():
    seeded = {"player_name": "A", "ranking": 10, "seed": 12}
    unseeded = {"player_name": "B", "ranking": 10, "seed": None}

    favorite, underdog = _derive_favorite_underdog(seeded, unseeded)
    assert favorite["player_name"] == "A"
    assert underdog["player_name"] == "B"


def test_equal_ranking_and_seed_keeps_original_order_without_crashing():
    player_a = {"player_name": "A", "ranking": 10, "seed": None}
    player_b = {"player_name": "B", "ranking": 10, "seed": None}

    favorite, underdog = _derive_favorite_underdog(player_a, player_b)
    assert favorite["player_name"] == "A"  # original order, deterministic
    assert underdog["player_name"] == "B"


def test_full_chain_still_matches_snapshot_fixture():
    """
    Integration: loader -> Match -> predict_upset() must still produce the
    exact output captured in tests/fixtures/predict_upset_snapshot.json,
    proving this refactor didn't silently change model behavior.
    """
    with open("tests/fixtures/predict_upset_snapshot.json", encoding="utf-8") as f:
        snapshot = json.load(f)

    matches = [Match(**m) for m in load_matches_raw()]
    for match in matches:
        prediction = predict_upset(match)
        expected = snapshot[match.match_id]
        assert prediction.favorite_win_probability == expected["favorite_win_probability"]
        assert prediction.upset_probability == expected["upset_probability"]
        assert prediction.risk_label == expected["risk_label"]
