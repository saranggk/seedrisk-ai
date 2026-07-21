"""
Tests for Unit U4 (engineered feature computation). See
docs/plans/2026-07-20-001-feat-real-wimbledon-backtest-data-plan.md.
"""

from datetime import date

from scripts.wimbledon_backtest.features import (
    _derive_favorite_underdog_safe,
    _tiebreak_win_pct,
    assemble_match_record,
    compute_player_features,
)
from scripts.wimbledon_backtest.history import HistoryRow


def _row(d, won, surface="Grass", tourney_name="Halle", score="6-3 6-4",
         own_svgms=10, own_bpsaved=2, own_bpfaced=3,
         opp_svgms=9, opp_bpsaved=1, opp_bpfaced=4, opponent_id=999):
    return HistoryRow(
        date=d, surface=surface, tourney_name=tourney_name, won=won,
        own_svgms=own_svgms, own_bpsaved=own_bpsaved, own_bpfaced=own_bpfaced,
        opp_svgms=opp_svgms, opp_bpsaved=opp_bpsaved, opp_bpfaced=opp_bpfaced,
        opponent_id=opponent_id, score=score,
    )


def test_hold_rate_hand_worked_example():
    index = {1: [_row(date(2022, 1, 1), won=True, own_svgms=10, own_bpsaved=2, own_bpfaced=3)]}
    # 5 grass matches needed to clear the thin-history threshold.
    index[1] = index[1] * 5

    features = compute_player_features(index, 1, date(2023, 1, 1), opponent_id=None)

    assert features["thin_grass_history"] is False
    assert features["surface_hold_rate"] == 0.9  # (10 - (3-2)) / 10


def test_break_rate_hand_worked_example():
    row = _row(date(2022, 1, 1), won=True, opp_svgms=8, opp_bpsaved=1, opp_bpfaced=5)
    index = {1: [row] * 5}

    features = compute_player_features(index, 1, date(2023, 1, 1), opponent_id=None)

    assert features["surface_break_rate"] == 0.5  # (5 - 1) / 8


def test_tiebreak_parsing_handles_multiple_formats_including_double_digit():
    rows = [
        _row(date(2022, 1, 1), won=True, score="7-6(4) 6-3"),   # player took the breaker
        _row(date(2022, 2, 1), won=True, score="3-6 6-7(5)"),   # player lost the breaker
        _row(date(2022, 3, 1), won=False, score="7-6(11) 4-6 6-3"),  # match winner took it; this player lost
        _row(date(2022, 4, 1), won=False, score="6-7(2) 7-5 4-6"),   # match loser (this player) took it
        _row(date(2022, 5, 1), won=True, score="6-2 6-3"),  # no tiebreak
    ]

    win_pct = _tiebreak_win_pct(rows)

    # 4 tiebreaks total: player won breakers in rows 1 and 4, lost in rows 2 and 3.
    assert win_pct == 0.5


def test_retirement_score_parses_without_crashing():
    rows = [_row(date(2022, 1, 1), won=True, score="6-2 3-0 RET")]

    win_pct = _tiebreak_win_pct(rows)

    assert win_pct is None  # no tiebreaks in a retirement with no breaker sets


def test_h2h_counts_only_meetings_before_as_of_not_the_target_match():
    index = {
        1: [
            _row(date(2021, 1, 1), won=True, opponent_id=2),
            _row(date(2023, 1, 1), won=False, opponent_id=2),
        ]
    }

    features = compute_player_features(index, 1, date(2022, 1, 1), opponent_id=2)

    assert features["h2h_wins"] == 1
    assert features["h2h_losses"] == 0


def test_player_below_thin_history_threshold_gets_null_grass_rates():
    index = {1: [_row(date(2022, 1, 1), won=True)] * 4}  # only 4 grass matches

    features = compute_player_features(index, 1, date(2023, 1, 1), opponent_id=None)

    assert features["thin_grass_history"] is True
    assert features["surface_win_pct"] is None
    assert features["surface_hold_rate"] is None
    assert features["surface_break_rate"] is None


def test_zero_prior_matches_nulls_out_rather_than_dividing_by_zero():
    features = compute_player_features({}, 1, date(2023, 1, 1), opponent_id=2)

    assert features["thin_grass_history"] is True
    assert features["surface_win_pct"] is None
    assert features["tournament_win_pct"] is None
    assert features["tiebreak_win_pct"] is None
    assert features["recent_win_pct"] is None
    assert features["last_10_record"] == "0-0"
    assert features["h2h_wins"] == 0
    assert features["h2h_losses"] == 0


def test_missing_rank_resolves_deterministically_not_a_crash():
    ranked = {"id": 1, "name": "Ranked", "seed": None, "ranking": 5}
    unranked = {"id": 2, "name": "Unranked", "seed": None, "ranking": None}

    favorite, underdog = _derive_favorite_underdog_safe(ranked, unranked)

    assert favorite is ranked
    assert underdog is unranked


def test_missing_rank_reversed_argument_order_still_resolves():
    ranked = {"id": 1, "name": "Ranked", "seed": None, "ranking": 5}
    unranked = {"id": 2, "name": "Unranked", "seed": None, "ranking": None}

    favorite, underdog = _derive_favorite_underdog_safe(unranked, ranked)

    assert favorite is ranked
    assert underdog is unranked


def test_assemble_match_record_with_real_missing_rank_case():
    """
    Mirrors the real WTA 2023 Wimbledon R128 case (Gasparyan vs Juvan) found
    during doc review: the loser's rank is missing from the source data.
    """
    target_match = {
        "match_id": "WTA-2023-540-153",
        "date": date(2023, 7, 3),
        "tour": "WTA",
        "round": "R128",
        "score": "6-4 6-2",
        "winner": {"id": 111, "name": "M. Gasparyan", "seed": None, "rank": 244},
        "loser": {"id": 222, "name": "K. Juvan", "seed": None, "rank": float("nan")},
    }

    record = assemble_match_record({}, target_match)

    # Neither rank comparison should crash; the ranked player (244) becomes favorite.
    assert record["favorite"]["player_name"] == "M. Gasparyan"
    assert record["underdog"]["player_name"] == "K. Juvan"
    assert record["actual_winner"] == "favorite"


def test_both_ranks_missing_resolves_by_seed_not_a_constant_underdog():
    """
    Regression test (code review, correctness + adversarial, corroborated):
    the both-ranks-missing branch of _derive_favorite_underdog_safe used to
    call the shared loader function on freshly-built copies, then compare
    the result by object identity against the ORIGINAL dicts -- an identity
    check that could never be True against a copy, so the seeded player was
    always mislabeled underdog regardless of the real seed tiebreak.
    """
    seeded = {"id": 1, "name": "Seeded", "seed": 3, "ranking": None}
    unseeded = {"id": 2, "name": "Unseeded", "seed": None, "ranking": None}

    favorite, underdog = _derive_favorite_underdog_safe(seeded, unseeded)

    # Mirrors _derive_favorite_underdog's own tie rule: a seed beats no seed.
    assert favorite is seeded
    assert underdog is unseeded


def test_assemble_match_record_both_ranks_missing_not_pinned_to_underdog():
    target_match = {
        "match_id": "ATP-2022-540-200",
        "date": date(2022, 7, 1),
        "tour": "ATP",
        "round": "R128",
        "score": "6-4 6-2",
        "winner": {"id": 111, "name": "Seeded Winner", "seed": 5, "rank": float("nan")},
        "loser": {"id": 222, "name": "Unseeded Loser", "seed": None, "rank": float("nan")},
    }

    record = assemble_match_record({}, target_match)

    # The winner is seeded, the loser isn't -- winner should resolve as
    # favorite (matching the shared seed tiebreak), not be pinned to underdog.
    assert record["favorite"]["player_name"] == "Seeded Winner"
    assert record["actual_winner"] == "favorite"


def test_assemble_match_record_happy_path_both_ranks_known():
    target_match = {
        "match_id": "ATP-2024-540-100",
        "date": date(2024, 7, 1),
        "tour": "ATP",
        "round": "R128",
        "score": "6-3 6-4",
        "winner": {"id": 1, "name": "Top Seed", "seed": 1, "rank": 1},
        "loser": {"id": 2, "name": "Qualifier", "seed": None, "rank": 250},
    }

    record = assemble_match_record({}, target_match)

    assert record["favorite"]["player_name"] == "Top Seed"
    assert record["underdog"]["player_name"] == "Qualifier"
    assert record["actual_winner"] == "favorite"


def test_assemble_match_record_underdog_wins():
    target_match = {
        "match_id": "ATP-2024-540-101",
        "date": date(2024, 7, 1),
        "tour": "ATP",
        "round": "R128",
        "score": "6-3 6-4",
        "winner": {"id": 2, "name": "Qualifier", "seed": None, "rank": 250},
        "loser": {"id": 1, "name": "Top Seed", "seed": 1, "rank": 1},
    }

    record = assemble_match_record({}, target_match)

    # The higher-ranked player (rank 1) is still the favorite by role, even
    # though they lost this match -- actual_winner must reflect the upset.
    assert record["favorite"]["player_name"] == "Top Seed"
    assert record["underdog"]["player_name"] == "Qualifier"
    assert record["actual_winner"] == "underdog"


def test_rate_features_compute_real_values_from_mixed_history():
    """
    The zero-history test proves these fields null out; this proves they
    compute a real, correct value from a populated, mixed-outcome history.
    """
    history = [
        _row(date(2020, 1, 1), won=True, tourney_name="Wimbledon", surface="Grass"),
        _row(date(2020, 7, 1), won=False, tourney_name="Wimbledon", surface="Grass"),
        _row(date(2022, 1, 1), won=True, tourney_name="Halle", surface="Grass"),
        _row(date(2022, 6, 1), won=True, tourney_name="Halle", surface="Grass"),
        _row(date(2022, 8, 1), won=False, tourney_name="US Open", surface="Hard"),
    ]
    index = {1: history}

    features = compute_player_features(index, 1, date(2023, 1, 1), opponent_id=None)

    assert features["tournament_win_pct"] == 0.5  # 1 win, 1 loss at Wimbledon
    assert features["last_10_record"] == "3-2"  # 3 wins, 2 losses overall


def test_recent_win_pct_respects_the_12_month_cutoff():
    history = [
        _row(date(2020, 1, 1), won=False),  # outside the 12-month window
        _row(date(2022, 6, 1), won=True),   # inside the 12-month window
    ]
    index = {1: history}

    features = compute_player_features(index, 1, date(2023, 1, 1), opponent_id=None)

    assert features["recent_win_pct"] == 1.0  # only the in-window win counts
