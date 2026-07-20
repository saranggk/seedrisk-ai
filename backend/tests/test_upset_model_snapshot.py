"""
Golden-file regression tests for the rule-based upset model.

WHY THIS EXISTS:
predict_upset() has no automated coverage otherwise, so a future weight/cap/
threshold edit (or a refactor like deriving favorite/underdog, or renaming
Player's surface fields) has no way to catch an accidental behavior change.
This snapshot captures today's actual output for all 16 sample matches and
fails loudly if a future change shifts a result. It is intentionally NOT a
test of whether the model's numbers are "right" -- only whether they changed.

Regenerating the snapshot after a deliberate model change:
    python -m tests.generate_snapshot   (see that script's docstring)
"""

import json
from pathlib import Path

from app.data.loader import load_matches_raw
from app.models import Match
from app.services.upset_model import predict_upset

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "predict_upset_snapshot.json"


def _load_snapshot() -> dict:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _current_predictions() -> dict:
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


def test_snapshot_covers_all_matches():
    snapshot = _load_snapshot()
    current = _current_predictions()
    assert set(snapshot.keys()) == set(current.keys()), (
        "The match IDs in the snapshot no longer match the dataset's match IDs -- "
        "regenerate the snapshot if this is an intentional dataset change."
    )


def test_predictions_match_snapshot():
    snapshot = _load_snapshot()
    current = _current_predictions()

    mismatches = []
    for match_id, expected in snapshot.items():
        actual = current.get(match_id)
        if actual != expected:
            mismatches.append(f"{match_id}: expected {expected}, got {actual}")

    assert not mismatches, (
        "predict_upset() output changed for the following matches "
        "(regenerate the fixture if this change was intentional):\n"
        + "\n".join(mismatches)
    )
