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


class FeatureContribution(BaseModel):
    """
    One scored factor that fed into the upset prediction.

    `impact` is signed: positive means this factor pushed upset_probability up,
    negative means it pushed upset_probability down. `direction` is just a
    human/UI-friendly restatement of that sign, so the frontend doesn't have
    to know the sign convention to render an up/down indicator.
    """

    feature: str
    label: str
    impact: float
    direction: str  # "increases_upset_risk" or "decreases_upset_risk"
    reason: str


class PredictionResponse(BaseModel):
    """API response for GET /matches/{match_id}/prediction."""

    match_id: str
    favorite_name: str
    underdog_name: str
    favorite_win_probability: float
    upset_probability: float
    risk_label: str
    top_factors: list[str]
    feature_contributions: list[FeatureContribution]
