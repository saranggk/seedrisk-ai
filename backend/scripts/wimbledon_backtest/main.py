"""
Orchestrates the real Wimbledon backtest data pipeline (Unit U5): fetch the
archive, identify target matches, build the history index, compute
engineered features, and write the output dataset plus a sanity-check
summary. See docs/plans/2026-07-20-001-feat-real-wimbledon-backtest-data-plan.md.

Run manually, once:

    cd backend && python -m scripts.wimbledon_backtest.main
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.wimbledon_backtest.features import assemble_match_record
from scripts.wimbledon_backtest.fetch import ensure_cloned
from scripts.wimbledon_backtest.history import build_history_index
from scripts.wimbledon_backtest.targets import load_target_matches

# data/ lives two levels above backend/scripts/, at the project root.
REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_FILE = REPO_ROOT / "data" / "wimbledon_backtest_matches.json"
SUMMARY_FILE = REPO_ROOT / "data" / "wimbledon_backtest_matches_summary.json"


def build_dataset() -> tuple[list[dict], dict]:
    archive_dir = ensure_cloned()
    targets = load_target_matches(archive_dir)
    index = build_history_index(archive_dir)

    records = [assemble_match_record(index, target) for target in targets]
    summary = _summarize(records)
    return records, summary


def _summarize(records: list[dict]) -> dict:
    dates = sorted(r["date"] for r in records)
    thin_sides = sum(
        1
        for r in records
        for role in ("favorite", "underdog")
        if r[role]["thin_grass_history"]
    )
    return {
        "match_count": len(records),
        "date_range": {"earliest": dates[0], "latest": dates[-1]} if dates else None,
        "thin_grass_history_flags": thin_sides,
        "thin_grass_history_flag_rate": (
            round(thin_sides / (len(records) * 2), 3) if records else None
        ),
    }


def main() -> None:
    records, summary = build_dataset()

    if not records:
        raise RuntimeError(
            "No target matches found -- refusing to overwrite any existing "
            f"{OUTPUT_FILE} with an empty dataset. Check the archive clone "
            "and the target year range in targets.py."
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, sort_keys=True)
        f.write("\n")

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")

    print(f"Wrote {summary['match_count']} matches to {OUTPUT_FILE}")
    print(
        f"Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}"
    )
    print(
        f"Thin grass-history flags: {summary['thin_grass_history_flags']} "
        f"player-sides ({summary['thin_grass_history_flag_rate']:.1%})"
    )


if __name__ == "__main__":
    main()
