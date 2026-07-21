"""
Identifies target Wimbledon matches for backtesting (Unit U2).

Reads the archive's atp_matches_<year>.csv / wta_matches_<year>.csv files for
TARGET_YEARS and filters to Wimbledon main-draw singles matches. Qualifying
files (*_qual_itf_*.csv) are never read -- they're a separate file, not a
round to filter out of the main file. See docs/plans/2026-07-20-001-feat-
real-wimbledon-backtest-data-plan.md, Unit U2 and KTD6.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.wimbledon_backtest._csv_source import iter_year_frames, parse_tourney_date

TARGET_YEARS = range(2021, 2026)
TOURS = ("atp", "wta")


def _clean(value):
    """Coerces a nullable numeric CSV field (seed/rank) to int, or None if missing.

    pandas reads seed/rank columns as float64 once any row has a missing
    value (NaN forces the whole column to float), so a present value like
    a rank of 1 otherwise round-trips as 1.0 into the output JSON.
    """
    return None if pd.isna(value) else int(value)


def _to_target_record(row, tour: str) -> dict:
    return {
        "match_id": f"{tour}-{row['tourney_id']}-{row['match_num']}",
        "date": parse_tourney_date(row["tourney_date"]),
        "tour": tour,
        "round": row["round"],
        "score": row["score"],
        "winner": {
            "id": row["winner_id"],
            "name": row["winner_name"],
            "seed": _clean(row["winner_seed"]),
            "rank": _clean(row["winner_rank"]),
        },
        "loser": {
            "id": row["loser_id"],
            "name": row["loser_name"],
            "seed": _clean(row["loser_seed"]),
            "rank": _clean(row["loser_rank"]),
        },
    }


def load_target_matches(archive_dir: Path) -> list[dict]:
    """Returns normalized Wimbledon main-draw singles match records for TARGET_YEARS."""
    records: list[dict] = []
    for tour in TOURS:
        for _year, df in iter_year_frames(archive_dir, tour, TARGET_YEARS):
            wimbledon = df[df["tourney_name"] == "Wimbledon"]
            wimbledon = wimbledon[wimbledon["score"] != "W/O"]
            records.extend(_to_target_record(row, tour.upper()) for _, row in wimbledon.iterrows())
    return records
