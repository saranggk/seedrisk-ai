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

from tests._snapshot import current_predictions

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "predict_upset_snapshot.json"


def _load_snapshot() -> dict:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_snapshot_covers_all_matches():
    snapshot = _load_snapshot()
    current = current_predictions()
    assert set(snapshot.keys()) == set(current.keys()), (
        "The match IDs in the snapshot no longer match the dataset's match IDs -- "
        "regenerate the snapshot if this is an intentional dataset change."
    )


def test_predictions_match_snapshot():
    snapshot = _load_snapshot()
    current = current_predictions()

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
