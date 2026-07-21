"""
Tests for Unit U2 (target Wimbledon match identification). See
docs/plans/2026-07-20-001-feat-real-wimbledon-backtest-data-plan.md.
"""

from datetime import date

import pandas as pd

from scripts.wimbledon_backtest.targets import load_target_matches

COLUMNS = [
    "tourney_id", "tourney_name", "surface", "draw_size", "tourney_level",
    "tourney_date", "match_num", "winner_id", "winner_seed", "winner_entry",
    "winner_name", "winner_hand", "winner_ht", "winner_ioc", "winner_age",
    "loser_id", "loser_seed", "loser_entry", "loser_name", "loser_hand",
    "loser_ht", "loser_ioc", "loser_age", "score", "best_of", "round",
    "minutes", "w_ace", "w_df", "w_svpt", "w_1stIn", "w_1stWon", "w_2ndWon",
    "w_SvGms", "w_bpSaved", "w_bpFaced", "l_ace", "l_df", "l_svpt", "l_1stIn",
    "l_1stWon", "l_2ndWon", "l_SvGms", "l_bpSaved", "l_bpFaced",
    "winner_rank", "winner_rank_points", "loser_rank", "loser_rank_points",
]


def _row(tourney_name, tourney_date, match_num, score, round_="R128", **overrides):
    base = {c: "" for c in COLUMNS}
    base.update({
        "tourney_id": f"{str(tourney_date)[:4]}-540",
        "tourney_name": tourney_name,
        "surface": "Grass",
        "tourney_level": "G",
        "tourney_date": tourney_date,
        "match_num": match_num,
        "winner_id": "100",
        "winner_name": "A. Winner",
        "winner_rank": 5,
        "loser_id": "200",
        "loser_name": "B. Loser",
        "loser_rank": 50,
        "score": score,
        "round": round_,
    })
    base.update(overrides)
    return base


def _write_csv(path, rows):
    pd.DataFrame(rows, columns=COLUMNS).to_csv(path, index=False)


def _make_archive(tmp_path, atp_rows_by_year=None, wta_rows_by_year=None):
    archive = tmp_path / "archive"
    for tour, rows_by_year in (("atp", atp_rows_by_year or {}), ("wta", wta_rows_by_year or {})):
        tour_dir = archive / tour
        tour_dir.mkdir(parents=True, exist_ok=True)
        for year, rows in rows_by_year.items():
            _write_csv(tour_dir / f"{tour}_matches_{year}.csv", rows)
    return archive


def test_keeps_only_wimbledon_rows(tmp_path):
    rows = [
        _row("Wimbledon", 20240701, 100, "6-3 6-4 3-6 6-3"),
        _row("Roland Garros", 20240601, 50, "6-2 6-2"),
    ]
    archive = _make_archive(tmp_path, atp_rows_by_year={2024: rows})

    records = load_target_matches(archive)

    assert len(records) == 1
    assert records[0]["match_id"] == "ATP-2024-540-100"


def test_excludes_walkover_keeps_retirement(tmp_path):
    rows = [
        _row("Wimbledon", 20240701, 101, "W/O"),
        _row("Wimbledon", 20240701, 102, "6-2 3-0 RET"),
    ]
    archive = _make_archive(tmp_path, atp_rows_by_year={2024: rows})

    records = load_target_matches(archive)

    assert len(records) == 1
    assert records[0]["score"] == "6-2 3-0 RET"


def test_both_tours_contribute(tmp_path):
    atp_rows = [_row("Wimbledon", 20240701, 100, "6-3 6-4")]
    wta_rows = [_row("Wimbledon", 20240701, 100, "6-3 6-4")]
    archive = _make_archive(tmp_path, atp_rows_by_year={2024: atp_rows}, wta_rows_by_year={2024: wta_rows})

    records = load_target_matches(archive)

    tours = {r["tour"] for r in records}
    assert tours == {"ATP", "WTA"}


def test_year_outside_window_not_included(tmp_path):
    rows = [_row("Wimbledon", 20260701, 100, "6-3 6-4")]
    archive = _make_archive(tmp_path, atp_rows_by_year={2026: rows})

    records = load_target_matches(archive)

    assert records == []


def test_record_shape_and_date_parsing(tmp_path):
    rows = [_row("Wimbledon", 20240715, 100, "6-3 6-4", round_="F")]
    archive = _make_archive(tmp_path, atp_rows_by_year={2024: rows})

    records = load_target_matches(archive)

    record = records[0]
    assert record["date"] == date(2024, 7, 15)
    assert record["round"] == "F"
    assert record["winner"] == {"id": 100, "name": "A. Winner", "seed": None, "rank": 5}
    assert record["loser"] == {"id": 200, "name": "B. Loser", "seed": None, "rank": 50}
