"""
Leakage-safe per-player match-history index (Unit U3).

Indexes 2016-2025 ATP + WTA matches (KTD2) by player_id, sorted by date, so
U4 can query "this player's matches strictly before date X" without any risk
of a target match's own outcome leaking into its own computed features
(R3). Walkovers are excluded (KTD6) -- they carry no real serve stats. See
docs/plans/2026-07-20-001-feat-real-wimbledon-backtest-data-plan.md.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

LOOKBACK_YEARS = range(2016, 2026)
TOURS = ("atp", "wta")


@dataclass(frozen=True)
class HistoryRow:
    """One match from a single player's perspective (`won` is relative to them)."""

    date: date
    surface: str
    tourney_name: str
    won: bool
    own_svgms: float
    own_bpsaved: float
    own_bpfaced: float
    opp_svgms: float
    opp_bpsaved: float
    opp_bpfaced: float
    opponent_id: object
    score: str


def _parse_tourney_date(raw) -> date:
    digits = str(int(raw))
    return date(int(digits[0:4]), int(digits[4:6]), int(digits[6:8]))


def build_history_index(archive_dir: Path) -> dict[object, list[HistoryRow]]:
    """Returns {player_id: [HistoryRow, ...]} sorted ascending by date."""
    index: dict[object, list[HistoryRow]] = defaultdict(list)
    for tour in TOURS:
        for year in LOOKBACK_YEARS:
            csv_path = archive_dir / tour / f"{tour}_matches_{year}.csv"
            if not csv_path.exists():
                continue
            _index_year(index, csv_path)
    for rows in index.values():
        rows.sort(key=lambda r: r.date)
    return dict(index)


def _index_year(index: dict, csv_path: Path) -> None:
    df = pd.read_csv(csv_path)
    df = df[df["score"] != "W/O"]
    for _, row in df.iterrows():
        _index_row(index, row)


def _index_row(index: dict, row) -> None:
    match_date = _parse_tourney_date(row["tourney_date"])
    surface = row["surface"]
    tourney_name = row["tourney_name"]
    score = row["score"]

    index[row["winner_id"]].append(
        HistoryRow(
            date=match_date,
            surface=surface,
            tourney_name=tourney_name,
            won=True,
            own_svgms=row["w_SvGms"],
            own_bpsaved=row["w_bpSaved"],
            own_bpfaced=row["w_bpFaced"],
            opp_svgms=row["l_SvGms"],
            opp_bpsaved=row["l_bpSaved"],
            opp_bpfaced=row["l_bpFaced"],
            opponent_id=row["loser_id"],
            score=score,
        )
    )
    index[row["loser_id"]].append(
        HistoryRow(
            date=match_date,
            surface=surface,
            tourney_name=tourney_name,
            won=False,
            own_svgms=row["l_SvGms"],
            own_bpsaved=row["l_bpSaved"],
            own_bpfaced=row["l_bpFaced"],
            opp_svgms=row["w_SvGms"],
            opp_bpsaved=row["w_bpSaved"],
            opp_bpfaced=row["w_bpFaced"],
            opponent_id=row["winner_id"],
            score=score,
        )
    )


def history_before(index: dict, player_id, as_of: date) -> list[HistoryRow]:
    """Returns player_id's matches strictly before as_of, in chronological order."""
    return [r for r in index.get(player_id, []) if r.date < as_of]
