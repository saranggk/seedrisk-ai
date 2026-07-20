"""
Regenerates tests/fixtures/predict_upset_snapshot.json from the current code.

Run this ONLY after a deliberate model change, then review the diff to
confirm the shift is the one you intended:

    cd backend && source venv/bin/activate && python -m tests.generate_snapshot
"""

import json
from pathlib import Path

from app.data.loader import load_matches_raw
from app.models import Match
from app.services.upset_model import predict_upset

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "predict_upset_snapshot.json"


def main() -> None:
    matches = [Match(**m) for m in load_matches_raw()]
    snapshot = {}
    for match in matches:
        prediction = predict_upset(match)
        snapshot[match.match_id] = {
            "favorite_win_probability": prediction.favorite_win_probability,
            "upset_probability": prediction.upset_probability,
            "risk_label": prediction.risk_label,
            "feature_contributions": [
                {"feature": fc.feature, "impact": fc.impact, "direction": fc.direction}
                for fc in prediction.feature_contributions
            ],
        }

    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Wrote snapshot for {len(snapshot)} matches to {FIXTURE_PATH}")


if __name__ == "__main__":
    main()
