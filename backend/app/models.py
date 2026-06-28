"""
Pydantic models for SeedRisk AI.

These models define the *shape* of a match/player as seen by the API.
They mirror the fields documented in docs/DATA_DICTIONARY.md.
"""

from pydantic import BaseModel


class Player(BaseModel):
    player_name: str
    ranking: int
    seed: int | None = None
    grass_win_pct: float
    recent_win_pct: float
    wimbledon_win_pct: float
    hold_rate_grass: float
    break_rate_grass: float
    tiebreak_win_pct: float
    last_10_record: str
    h2h_wins: int
    h2h_losses: int


class Match(BaseModel):
    """Core match record: a favorite vs. an underdog, as stored in the dataset."""

    match_id: str
    round: str
    favorite: Player
    underdog: Player


class MatchResponse(Match):
    """
    The shape returned by the API for a single match.

    Right now this is identical to Match — it exists as its own model so that
    later phases (e.g. Phase 4's prediction fields) can extend the API response
    without changing the underlying stored Match shape.
    """

    pass
