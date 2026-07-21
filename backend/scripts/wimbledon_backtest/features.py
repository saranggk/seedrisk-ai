"""
Engineered feature computation per target match (Unit U4). See
docs/plans/2026-07-20-001-feat-real-wimbledon-backtest-data-plan.md.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

import pandas as pd

from app.data.loader import _derive_favorite_underdog
from scripts.wimbledon_backtest.history import HistoryRow, history_before

THIN_HISTORY_MIN_GRASS_MATCHES = 5
RECENT_FORM_WINDOW_DAYS = 365
# Multi-digit tiebreak point counts are real (e.g. "7-6(11)"), so \d+, not \d.
_TIEBREAK_TOKEN = re.compile(r"(6-7|7-6)\(\d+\)")


def _rate(wins: int, total: int) -> float | None:
    return (wins / total) if total else None


def _win_rate(rows: list[HistoryRow]) -> float | None:
    return _rate(sum(1 for r in rows if r.won), len(rows))


def _surface_win_pct(grass_history: list[HistoryRow]) -> float | None:
    return _win_rate(grass_history)


def _tournament_win_pct(history: list[HistoryRow]) -> float | None:
    return _win_rate([r for r in history if r.tourney_name == "Wimbledon"])


def _recent_win_pct(history: list[HistoryRow], as_of: date) -> float | None:
    cutoff = as_of - timedelta(days=RECENT_FORM_WINDOW_DAYS)
    return _win_rate([r for r in history if r.date >= cutoff])


def _hold_rate(grass_history: list[HistoryRow]) -> float | None:
    if not grass_history:
        return None
    num = sum(r.own_svgms - (r.own_bpfaced - r.own_bpsaved) for r in grass_history)
    den = sum(r.own_svgms for r in grass_history)
    return (num / den) if den else None


def _break_rate(grass_history: list[HistoryRow]) -> float | None:
    if not grass_history:
        return None
    num = sum(r.opp_bpfaced - r.opp_bpsaved for r in grass_history)
    den = sum(r.opp_svgms for r in grass_history)
    return (num / den) if den else None


def _tiebreak_win_pct(history: list[HistoryRow]) -> float | None:
    wins = 0
    total = 0
    for r in history:
        for set_token in _TIEBREAK_TOKEN.findall(r.score):
            total += 1
            # Sets are written from the match winner's perspective: "7-6"
            # means the match winner took that set's breaker, "6-7" means
            # the match loser did.
            winner_took_breaker = set_token == "7-6"
            player_took_breaker = winner_took_breaker if r.won else not winner_took_breaker
            if player_took_breaker:
                wins += 1
    return _rate(wins, total)


def _last_10_record(history: list[HistoryRow]) -> str:
    recent = history[-10:]
    wins = sum(1 for r in recent if r.won)
    return f"{wins}-{len(recent) - wins}"


def _h2h(history: list[HistoryRow], opponent_id) -> tuple[int, int]:
    matchups = [r for r in history if r.opponent_id == opponent_id]
    wins = sum(1 for r in matchups if r.won)
    return wins, len(matchups) - wins


def compute_player_features(index: dict, player_id, as_of: date, opponent_id) -> dict:
    """Computes one player's engineered features from their as-of history (R2, R3)."""
    history = history_before(index, player_id, as_of)
    grass_history = [r for r in history if r.surface == "Grass"]
    thin_grass_history = len(grass_history) < THIN_HISTORY_MIN_GRASS_MATCHES
    h2h_wins, h2h_losses = _h2h(history, opponent_id)

    return {
        "surface_win_pct": None if thin_grass_history else _surface_win_pct(grass_history),
        "surface_hold_rate": None if thin_grass_history else _hold_rate(grass_history),
        "surface_break_rate": None if thin_grass_history else _break_rate(grass_history),
        "tournament_win_pct": _tournament_win_pct(history),
        "recent_win_pct": _recent_win_pct(history, as_of),
        "tiebreak_win_pct": _tiebreak_win_pct(history),
        "last_10_record": _last_10_record(history),
        "h2h_wins": h2h_wins,
        "h2h_losses": h2h_losses,
        "thin_grass_history": thin_grass_history,
    }


def _coerce_rank(value):
    return None if pd.isna(value) else int(value)


def _derive_favorite_underdog_safe(player_a: dict, player_b: dict) -> tuple[dict, dict]:
    """
    Wraps loader.py's _derive_favorite_underdog for missing ranks (KTD9).

    That function assumes `ranking` is always present -- true for the live
    app's JSON data (Player.ranking is a required field there), not true for
    real CSV data with missing ranks (e.g. WTA 2023 Wimbledon R128,
    Gasparyan vs Juvan, has an empty loser_rank). A `None` ranking would hit
    an unguarded `None < int` comparison inside that function and raise
    TypeError, so a missing rank is resolved here first: the ranked player
    is favorite over an unranked one; if both are missing, fall back to the
    shared function's own seed/tie logic via an equal placeholder ranking.
    """
    rank_a, rank_b = player_a["ranking"], player_b["ranking"]
    if rank_a is not None and rank_b is not None:
        return _derive_favorite_underdog(player_a, player_b)
    if rank_a is not None:
        return (player_a, player_b)
    if rank_b is not None:
        return (player_b, player_a)
    # Both missing: the shared function needs a non-None ranking to compare,
    # so it's called on copies with an equal placeholder ranking -- but its
    # result is then one of those COPIES, never player_a/player_b themselves.
    # A caller doing an `is` identity check against the originals (as
    # assemble_match_record does) would always get False here, silently
    # forcing "underdog" regardless of the real seed tiebreak. Compare by id
    # instead, then return the original objects in the resolved order.
    placeholder_favorite, _ = _derive_favorite_underdog(
        {**player_a, "ranking": 0}, {**player_b, "ranking": 0}
    )
    a_is_favorite = placeholder_favorite["id"] == player_a["id"]
    return (player_a, player_b) if a_is_favorite else (player_b, player_a)


def assemble_match_record(index: dict, target_match: dict) -> dict:
    """Builds one backtest record: both sides' features plus which side actually won (R4)."""
    winner = target_match["winner"]
    loser = target_match["loser"]
    as_of = target_match["date"]

    winner_features = compute_player_features(index, winner["id"], as_of, loser["id"])
    loser_features = compute_player_features(index, loser["id"], as_of, winner["id"])

    winner_for_derivation = {**winner, "ranking": _coerce_rank(winner["rank"])}
    loser_for_derivation = {**loser, "ranking": _coerce_rank(loser["rank"])}

    favorite_side, underdog_side = _derive_favorite_underdog_safe(
        winner_for_derivation, loser_for_derivation
    )
    winner_is_favorite = favorite_side is winner_for_derivation

    favorite_source = winner if winner_is_favorite else loser
    underdog_source = loser if winner_is_favorite else winner
    favorite_features = winner_features if winner_is_favorite else loser_features
    underdog_features = loser_features if winner_is_favorite else winner_features

    return {
        "match_id": target_match["match_id"],
        "date": target_match["date"].isoformat(),
        "tour": target_match["tour"],
        "round": target_match["round"],
        "actual_winner": "favorite" if winner_is_favorite else "underdog",
        "favorite": {
            "player_name": favorite_source["name"],
            "ranking": favorite_source["rank"],
            "seed": favorite_source["seed"],
            **favorite_features,
        },
        "underdog": {
            "player_name": underdog_source["name"],
            "ranking": underdog_source["rank"],
            "seed": underdog_source["seed"],
            **underdog_features,
        },
    }
