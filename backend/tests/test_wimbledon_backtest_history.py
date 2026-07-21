"""
Tests for Unit U3 (leakage-safe player match-history index). See
docs/plans/2026-07-20-001-feat-real-wimbledon-backtest-data-plan.md.
"""

from datetime import date

import pandas as pd

from scripts.wimbledon_backtest.history import build_history_index, history_before

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


def _row(tourney_date, winner_id, loser_id, score="6-3 6-4", surface="Grass", tourney_name="Halle"):
    base = {c: "" for c in COLUMNS}
    base.update({
        "tourney_id": f"{str(tourney_date)[:4]}-001",
        "tourney_name": tourney_name,
        "surface": surface,
        "tourney_level": "A",
        "tourney_date": tourney_date,
        "match_num": 1,
        "winner_id": winner_id,
        "winner_name": f"Player {winner_id}",
        "loser_id": loser_id,
        "loser_name": f"Player {loser_id}",
        "score": score,
        "round": "F",
        "w_SvGms": 10, "w_bpSaved": 2, "w_bpFaced": 3,
        "l_SvGms": 9, "l_bpSaved": 1, "l_bpFaced": 4,
    })
    return base


def _archive(tmp_path, rows_by_year, tour="atp"):
    archive = tmp_path / "archive"
    tour_dir = archive / tour
    tour_dir.mkdir(parents=True, exist_ok=True)
    for year, rows in rows_by_year.items():
        pd.DataFrame(rows, columns=COLUMNS).to_csv(tour_dir / f"{tour}_matches_{year}.csv", index=False)
    return archive


def test_history_before_returns_chronological_order(tmp_path):
    rows = [
        _row(20220301, winner_id=1, loser_id=2),
        _row(20220101, winner_id=1, loser_id=3),
        _row(20220601, winner_id=1, loser_id=4),
    ]
    archive = _archive(tmp_path, {2022: rows})
    index = build_history_index(archive)

    history = history_before(index, 1, date(2022, 12, 31))

    assert [h.date for h in history] == [date(2022, 1, 1), date(2022, 3, 1), date(2022, 6, 1)]


def test_as_of_boundary_is_strict_not_inclusive(tmp_path):
    rows = [_row(20220601, winner_id=1, loser_id=2)]
    archive = _archive(tmp_path, {2022: rows})
    index = build_history_index(archive)

    on_date = history_before(index, 1, date(2022, 6, 1))
    after_date = history_before(index, 1, date(2022, 6, 2))

    assert on_date == []
    assert len(after_date) == 1


def test_player_with_no_prior_matches_returns_empty(tmp_path):
    archive = _archive(tmp_path, {2022: [_row(20220601, winner_id=1, loser_id=2)]})
    index = build_history_index(archive)

    history = history_before(index, 999, date(2022, 12, 31))

    assert history == []


def test_player_indexed_under_both_winner_and_loser_roles(tmp_path):
    rows = [
        _row(20220101, winner_id=1, loser_id=2),
        _row(20220301, winner_id=2, loser_id=1),
    ]
    archive = _archive(tmp_path, {2022: rows})
    index = build_history_index(archive)

    history = history_before(index, 1, date(2022, 12, 31))

    assert len(history) == 2
    assert history[0].won is True
    assert history[1].won is False


def test_walkover_excluded_from_index(tmp_path):
    rows = [
        _row(20220101, winner_id=1, loser_id=2, score="W/O"),
        _row(20220301, winner_id=1, loser_id=3, score="6-2 6-2"),
    ]
    archive = _archive(tmp_path, {2022: rows})
    index = build_history_index(archive)

    history = history_before(index, 1, date(2022, 12, 31))

    assert len(history) == 1
    assert history[0].date == date(2022, 3, 1)


def test_serve_stats_recorded_from_each_players_own_perspective(tmp_path):
    rows = [_row(20220101, winner_id=1, loser_id=2)]
    archive = _archive(tmp_path, {2022: rows})
    index = build_history_index(archive)

    winner_history = history_before(index, 1, date(2022, 12, 31))[0]
    loser_history = history_before(index, 2, date(2022, 12, 31))[0]

    assert winner_history.own_svgms == 10
    assert winner_history.opp_svgms == 9
    assert loser_history.own_svgms == 9
    assert loser_history.opp_svgms == 10
