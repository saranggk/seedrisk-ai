"""Shared CSV-source helpers for targets.py and history.py -- both read the
same archive/<tour>/<tour>_matches_<year>.csv layout and the same
tourney_date encoding, so this is factored out to avoid drift between them.
"""

from __future__ import annotations

import warnings
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd

TOURS = ("atp", "wta")
WALKOVER_SCORE = "W/O"


def parse_tourney_date(raw) -> date:
    digits = str(int(raw))
    return date(int(digits[0:4]), int(digits[4:6]), int(digits[6:8]))


def iter_year_frames(archive_dir: Path, tour: str, years: Iterable[int]):
    """Yields (year, DataFrame) for each existing matches_<year>.csv under tour/.

    A missing file for a *requested* year is a silent gap in the resulting
    dataset -- warn loudly rather than letting the run quietly proceed on
    less data than the caller asked for.
    """
    for year in years:
        csv_path = archive_dir / tour / f"{tour}_matches_{year}.csv"
        if csv_path.exists():
            yield year, pd.read_csv(csv_path)
        else:
            warnings.warn(
                f"Expected {csv_path} not found -- {tour} {year} is missing "
                "from the resulting dataset.",
                stacklevel=2,
            )
