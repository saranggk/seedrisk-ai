"""
Regenerates tests/fixtures/predict_upset_snapshot.json from the current code.

Run this ONLY after a deliberate model change, then review the diff to
confirm the shift is the one you intended:

    cd backend && source venv/bin/activate && python -m tests.generate_snapshot
"""

import json
from pathlib import Path

from tests._snapshot import current_predictions

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "predict_upset_snapshot.json"


def main() -> None:
    snapshot = current_predictions()

    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Wrote snapshot for {len(snapshot)} matches to {FIXTURE_PATH}")


if __name__ == "__main__":
    main()
