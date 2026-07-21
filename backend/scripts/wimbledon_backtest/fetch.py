"""
Clones the archival mirror of Jeff Sackmann's tennis data (see
docs/plans/2026-07-20-001-feat-real-wimbledon-backtest-data-plan.md, KTD1)
into a gitignored scratch directory.

WHY THIS MIRROR, NOT THE ORIGINAL REPOS:
github.com/JeffSackmann/tennis_atp and tennis_wta returned HTTP 404 as of
planning time -- his account now hosts only tennis_MatchChartingProject.
Aneeshers/tennis-sackmann-archive is a same-license (CC BY-NC-SA 4.0),
data-only snapshot taken directly from those repos in June 2026, with a
verified matching column structure. If this mirror also disappears, search
GitHub for other forks/mirrors of "tennis_atp" or "tennis-sackmann", sorted
by recency, and look for one with a README that documents its upstream
commit provenance (as this one does).

Run this manually, once, before running the rest of the pipeline:

    cd backend && python -m scripts.wimbledon_backtest.fetch
"""

import subprocess
from pathlib import Path

MIRROR_URL = "https://github.com/Aneeshers/tennis-sackmann-archive.git"

# .data-cache/ lives at the project root, two levels above backend/scripts/.
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRATCH_DIR = REPO_ROOT / ".data-cache" / "tennis-sackmann-archive"

REQUIRED_PATHS = [
    SCRATCH_DIR / "atp",
    SCRATCH_DIR / "atp" / "matches_data_dictionary.txt",
    SCRATCH_DIR / "wta",
]


def ensure_cloned() -> Path:
    """Clones the mirror into SCRATCH_DIR if not already present; returns SCRATCH_DIR."""
    if SCRATCH_DIR.exists():
        _verify_structure()
        return SCRATCH_DIR

    SCRATCH_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", MIRROR_URL, str(SCRATCH_DIR)],
        check=True,
    )
    _verify_structure()
    return SCRATCH_DIR


def _verify_structure() -> None:
    missing = [str(p) for p in REQUIRED_PATHS if not p.exists()]
    if missing:
        raise RuntimeError(
            "Cloned archive is missing expected paths: "
            + ", ".join(missing)
            + f". Expected atp/ and wta/ folders under {SCRATCH_DIR}."
        )


if __name__ == "__main__":
    path = ensure_cloned()
    print(f"Archive ready at {path}")
