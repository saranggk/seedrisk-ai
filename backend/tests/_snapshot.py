"""
Shared serialization for the predict_upset() golden-file snapshot.

Both test_upset_model_snapshot.py (reads the snapshot) and generate_snapshot.py
(writes it) need the exact same dict shape -- extracted here so a future field
addition/rename can't update one and silently drift from the other.
"""

from app.data.loader import load_matches_raw
from app.models import Match
from app.services.upset_model import predict_upset


def current_predictions() -> dict:
    matches = [Match(**m) for m in load_matches_raw()]
    result = {}
    for match in matches:
        prediction = predict_upset(match)
        result[match.match_id] = {
            "favorite_win_probability": prediction.favorite_win_probability,
            "upset_probability": prediction.upset_probability,
            "risk_label": prediction.risk_label,
            "feature_contributions": [
                {"feature": fc.feature, "impact": fc.impact, "direction": fc.direction}
                for fc in prediction.feature_contributions
            ],
        }
    return result
