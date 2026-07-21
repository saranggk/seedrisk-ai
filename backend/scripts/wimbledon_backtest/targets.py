"""
Identifies target Wimbledon matches for backtesting (Unit U2).

Reads the archive's atp_matches_<year>.csv / wta_matches_<year>.csv files for
TARGET_YEARS and filters to Wimbledon main-draw singles matches. Qualifying
files (*_qual_itf_*.csv) are never read -- they're a separate file, not a
round to filter out of the main file. See docs/plans/2026-07-20-001-feat-
real-wimbledon-backtest-data-plan.md, Unit U2 and KTD6.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

TARGET_YEARS = range(2021, 2026)
TOURS = ("atp", "wta")


def _parse_tourney_date(raw) -> date:
    digits = str(int(raw))
    return date(int(digits[0:4]), int(digits[4:6]), int(digits[6:8]))


def _clean(value):
    return None if pd.isna(value) else value


def _to_target_record(row, tour: str) -> dict:
    return {
        "match_id": f"{tour}-{row['tourney_id']}-{row['match_num']}",
        "date": _parse_tourney_date(row["tourney_date"]),
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
        for year in TARGET_YEARS:
            csv_path = archive_dir / tour / f"{tour}_matches_{year}.csv"
            if not csv_path.exists():
                continue
            records.extend(_load_year(csv_path, tour.upper()))
    return records


def _load_year(csv_path: Path, tour: str) -> list[dict]:
    df = pd.read_csv(csv_path)
    wimbledon = df[df["tourney_name"] == "Wimbledon"]
    wimbledon = wimbledon[wimbledon["score"] != "W/O"]
    return [_to_target_record(row, tour) for _, row in wimbledon.iterrows()]
