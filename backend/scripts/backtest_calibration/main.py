"""
Orchestrates the backtest calibration harness (Unit U4): load the real
Wimbledon backtest dataset, filter to scoreable matches, score them against
predict_upset(), compute calibration metrics, and write the committed report.
See docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.

Run manually, whenever the dataset changes:

    cd backend && python -m scripts.backtest_calibration.main
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.backtest_calibration.loader import DATA_FILE, load_records, filter_scoreable
from scripts.backtest_calibration.metrics import compute_metrics
from scripts.backtest_calibration.scoring import score_matches

# data/ lives three levels above backend/scripts/backtest_calibration/, at the project root.
REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_FILE = REPO_ROOT / "data" / "calibration_report.json"


def build_report(records: list[dict]) -> dict:
    """Runs the full loader -> scoring -> metrics pipeline over raw records."""
    scored_matches, excluded_count = filter_scoreable(records)
    results = score_matches(scored_matches)
    metrics = compute_metrics(results)

    return {
        "total_count": len(records),
        "scored_count": len(scored_matches),
        "excluded_count": excluded_count,
        **metrics,
    }


def write_report(report: dict, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")


def main() -> None:
    records = load_records(DATA_FILE)
    report = build_report(records)
    write_report(report, OUTPUT_FILE)

    print(f"Scored {report['scored_count']} of {report['total_count']} matches "
          f"({report['excluded_count']} excluded) -> {OUTPUT_FILE}")
    if report["scored_count"] == 0:
        print("No scoreable matches -- nothing further to report.")
        return
    print(f"Overall Brier score: {report['brier_score']:.4f}")
    for tour, breakdown in report["by_tour"].items():
        if breakdown["count"]:
            print(f"  {tour}: {breakdown['count']} matches, Brier {breakdown['brier_score']:.4f}")
    for label, breakdown in report["by_risk_label"].items():
        if breakdown["count"]:
            print(
                f"  {label}: {breakdown['count']} matches, "
                f"observed upset rate {breakdown['observed_upset_rate']:.3f}"
            )


if __name__ == "__main__":
    main()
