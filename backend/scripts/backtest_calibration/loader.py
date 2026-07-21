"""
Load and filter the real Wimbledon backtest dataset for scoring (Unit U1).

Reads data/wimbledon_backtest_matches.json and splits it into matches that
have every field predict_upset() reads (scoreable) and matches that don't
(excluded, counted but not scored -- R1, R2). See
docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from app.models import Match, Player

# data/ lives three levels above backend/scripts/backtest_calibration/, at the project root.
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_FILE = REPO_ROOT / "data" / "wimbledon_backtest_matches.json"

REQUIRED_PLAYER_FIELDS = (
    "ranking",
    "surface_win_pct",
    "recent_win_pct",
    "tournament_win_pct",
    "surface_hold_rate",
    "surface_break_rate",
    "tiebreak_win_pct",
)


@dataclass(frozen=True)
class ScoredMatch:
    """A scoreable Match plus the ground truth and tour predict_upset() doesn't carry."""

    match: Match
    actual_winner: str  # "favorite" or "underdog"
    tour: str  # "ATP" or "WTA"


def _is_missing(value) -> bool:
    """True for None or NaN -- the real dataset encodes some missing grass
    rates as NaN, not null (KTD3), so an is-None-only check would miss them."""
    return value is None or (isinstance(value, float) and math.isnan(value))


def _has_all_required_fields(player: dict) -> bool:
    return all(not _is_missing(player.get(field)) for field in REQUIRED_PLAYER_FIELDS)


def load_records(path: Path | None = None) -> list[dict]:
    """Load the backtest dataset as a plain list of match dicts."""
    with open(path or DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def filter_scoreable(records: list[dict]) -> tuple[list[ScoredMatch], int]:
    """
    Splits raw backtest records into scoreable ScoredMatch objects and an
    excluded count. A record is scoreable only when both its favorite and
    underdog have every field predict_upset() reads (R1); otherwise it's
    excluded and counted, not silently dropped (R2).
    """
    scored: list[ScoredMatch] = []
    excluded_count = 0

    for record in records:
        favorite, underdog = record["favorite"], record["underdog"]
        if not (_has_all_required_fields(favorite) and _has_all_required_fields(underdog)):
            excluded_count += 1
            continue

        match = Match(
            match_id=record["match_id"],
            round=record["round"],
            favorite=Player(**favorite),
            underdog=Player(**underdog),
        )
        scored.append(
            ScoredMatch(match=match, actual_winner=record["actual_winner"], tour=record["tour"])
        )

    return scored, excluded_count
