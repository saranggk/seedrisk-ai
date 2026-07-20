"""
Pydantic models for SeedRisk AI.

These models define the *shape* of a match/player as seen by the API.
They mirror the fields documented in docs/DATA_DICTIONARY.md.
"""

from typing import Literal

from pydantic import BaseModel


class Player(BaseModel):
    player_name: str
    ranking: int
    seed: int | None = None
    surface_win_pct: float
    recent_win_pct: float
    tournament_win_pct: float
    surface_hold_rate: float
    surface_break_rate: float
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
    negative means it pushed upset_probability down, and exactly 0 means it had
    no effect. `direction` is a human/UI-friendly restatement of that sign, so
    the frontend doesn't have to know the sign convention to render an
    up/down/neutral indicator.
    """

    feature: str
    label: str
    impact: float
    direction: str  # "increases_upset_risk", "decreases_upset_risk", or "neutral" (impact == 0)
    reason: str


class PredictionResponse(BaseModel):
    """API response for GET /matches/{match_id}/prediction."""

    match_id: str
    favorite_name: str
    underdog_name: str
    favorite_win_probability: float
    upset_probability: float
    risk_label: str
    # The 3 largest model factors by absolute impact — i.e. the biggest
    # prediction drivers, not necessarily "reasons the underdog could win."
    # A factor can be a top_factor because it strongly protects the favorite
    # (e.g. a big ranking gap), not just because it threatens them.
    top_factors: list[str]
    feature_contributions: list[FeatureContribution]


class AnalystReportFields(BaseModel):
    """
    The explanatory fields produced by the analyst layer (Phase 6) — either
    Claude or the deterministic mock generator. This is deliberately just the
    prose explanation: it carries no probabilities or labels of its own, and
    nothing here can override favorite_win_probability, upset_probability,
    risk_label, top_factors, or feature_contributions from PredictionResponse.
    """

    match_summary: str
    why_favorite_is_favored: str
    why_upset_could_happen: str
    key_stat_to_watch: str
    upset_recipe: list[str]
    final_take: str
    confidence_note: str


class AnalystReportResponse(AnalystReportFields):
    """API response for POST /matches/{match_id}/analysis."""

    # "claude" when ANTHROPIC_API_KEY is set and the call succeeded, "mock"
    # otherwise — so the frontend can show a "demo mode" note when relevant.
    source: Literal["claude", "mock"]


# ---------------------------------------------------------------------------
# Picks analysis models (Phase 8 — picks + Claude portfolio analysis)
# ---------------------------------------------------------------------------


class PickItem(BaseModel):
    """A single user pick: which match and which side they chose."""

    match_id: str
    choice: Literal["favorite", "upset"]


class PicksAnalysisRequest(BaseModel):
    """Request body for POST /picks/analysis."""

    picks: list[PickItem]


class PicksAnalysisFields(BaseModel):
    """
    The prose fields written by Claude (or the mock generator) for a picks analysis.
    No numeric fields — grade and stats are pre-computed in Python and cannot be
    overridden here, same as how AnalystReportFields cannot override the model's numbers.
    """

    slate_summary: str
    boldest_pick: str
    best_aligned_pick: str
    portfolio_note: str


class PicksAnalysisResponse(PicksAnalysisFields):
    """API response for POST /picks/analysis."""

    slate_grade: Literal["Aggressive", "Balanced", "Conservative"]
    picks_count: int
    expected_correct: float
    source: Literal["claude", "mock"]
