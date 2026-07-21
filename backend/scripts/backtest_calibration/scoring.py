"""
Score scoreable matches against the real predict_upset() model (Unit U2).

Runs app.services.upset_model.predict_upset() unmodified (KTD2) and records
predicted vs. actual outcome per match. See
docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.
"""

from __future__ import annotations

from app.services.upset_model import predict_upset
from scripts.backtest_calibration.loader import ScoredMatch


def score_matches(scored_matches: list[ScoredMatch]) -> list[dict]:
    """
    Runs predict_upset() on each ScoredMatch and returns one result dict per
    match: match_id, tour, risk_label, favorite_win_probability, outcome
    (1 if the favorite actually won, else 0), and squared_error (R3).
    """
    results = []
    for scored in scored_matches:
        prediction = predict_upset(scored.match)
        outcome = 1 if scored.actual_winner == "favorite" else 0
        squared_error = (prediction.favorite_win_probability - outcome) ** 2

        results.append(
            {
                "match_id": scored.match.match_id,
                "tour": scored.tour,
                "risk_label": prediction.risk_label,
                "favorite_win_probability": prediction.favorite_win_probability,
                "outcome": outcome,
                "squared_error": squared_error,
            }
        )
    return results
