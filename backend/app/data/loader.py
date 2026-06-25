"""
Phase 1 data-loading utility.

This module does NOT run a server and does NOT touch SQLite yet (that's Phase 2).
Its only job is to read data/sample_matches.json into Python so it can be
inspected, tested, and later reused by the FastAPI app and the scoring model.
"""

import json
from pathlib import Path

import pandas as pd

# data/ lives two levels above backend/app/data/, at the project root.
DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "sample_matches.json"


def load_matches_raw() -> list[dict]:
    """Load sample_matches.json as a plain list of match dicts (favorite/underdog nested)."""
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_matches_flat() -> pd.DataFrame:
    """
    Flatten each match into one row per player, tagged with role ('favorite' or 'underdog')
    and match_id/round, so it's easy to inspect or feed into pandas-based feature engineering
    in a later phase.
    """
    matches = load_matches_raw()
    rows = []
    for match in matches:
        for role in ("favorite", "underdog"):
            row = {"match_id": match["match_id"], "round": match["round"], "role": role}
            row.update(match[role])
            rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    # Quick manual check: `python -m app.data.loader` from backend/
    df = load_matches_flat()
    print(f"Loaded {df['match_id'].nunique()} matches, {len(df)} player rows.\n")
    print(df[["match_id", "round", "role", "player_name", "ranking", "seed"]])
