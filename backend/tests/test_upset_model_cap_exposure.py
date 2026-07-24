"""
Coverage for FeatureContribution.max_impact -- the fixed ceiling each factor's
impact is scaled against, exposed so the frontend can render zero-anchored
bars that are comparable across matches instead of scaling relative to
whatever the largest impact happens to be in a single match's list.
"""

from app.data.loader import load_matches_raw
from app.models import Match
from app.services.upset_model import predict_upset

EXPECTED_CAPS = {
    "ranking_gap": 0.10,
    "surface_win_pct": 0.08,
    "recent_win_pct": 0.07,
    "tournament_win_pct": 0.06,
    "surface_hold_rate": 0.06,
    "surface_break_rate": 0.07,
    "tiebreak_win_pct": 0.05,
    "h2h_edge": 0.09,
}


def _all_predictions():
    matches = [Match(**m) for m in load_matches_raw()]
    return [predict_upset(match) for match in matches]


def test_each_factor_max_impact_matches_its_documented_cap():
    predictions = _all_predictions()
    assert predictions, "expected at least one sample match"
    for prediction in predictions:
        for contribution in prediction.feature_contributions:
            expected = EXPECTED_CAPS[contribution.feature]
            assert contribution.max_impact == expected, (
                f"{contribution.feature} in {prediction.match_id}: "
                f"expected max_impact={expected}, got {contribution.max_impact}"
            )


def test_impact_never_exceeds_its_own_max_impact():
    for prediction in _all_predictions():
        for contribution in prediction.feature_contributions:
            assert abs(contribution.impact) <= contribution.max_impact, (
                f"{contribution.feature} in {prediction.match_id}: "
                f"impact {contribution.impact} exceeds max_impact {contribution.max_impact}"
            )
