"""
Aggregate scored results into calibration metrics (Unit U3): overall Brier
score, a reliability diagram, and breakdowns by tour and by risk label. See
docs/plans/2026-07-21-001-feat-backtest-calibration-harness-plan.md.
"""

from __future__ import annotations

import math

TOURS = ("ATP", "WTA")

# Must match the risk_label values app/services/upset_model.py's
# _determine_risk_label() can return.
RISK_LABELS = ("Low", "Medium", "High", "Trap Match")

# Reliability bins are fixed-width and derived from the data's own observed
# range at run time, not hardcoded from upset_model.py's clamp constants
# (KTD4), so this stays accurate if that model's clamp range changes later.
BIN_WIDTH = 0.05


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _brier_score(results: list[dict]) -> float | None:
    return _mean([r["squared_error"] for r in results])


def _bin_edges(values: list[float]) -> list[float]:
    # round() before floor/ceil absorbs float division noise (e.g.
    # 0.6 / 0.05 == 11.999999999999998, not 12) that would otherwise put a
    # bin-aligned value in the wrong bin -- caught by a real test failure.
    lo = math.floor(round(min(values) / BIN_WIDTH, 8)) * BIN_WIDTH
    hi = math.ceil(round(max(values) / BIN_WIDTH, 8)) * BIN_WIDTH
    if hi == lo:
        hi = lo + BIN_WIDTH
    n_bins = round((hi - lo) / BIN_WIDTH)
    return [round(lo + i * BIN_WIDTH, 10) for i in range(n_bins + 1)]


def _bin_index(value: float, edges: list[float]) -> int:
    for i in range(len(edges) - 1):
        if edges[i] <= value < edges[i + 1]:
            return i
    return len(edges) - 2  # the max value lands in the last bin, inclusive


def _reliability_bins(results: list[dict]) -> list[dict]:
    if not results:
        return []

    edges = _bin_edges([r["favorite_win_probability"] for r in results])
    buckets: list[list[dict]] = [[] for _ in range(len(edges) - 1)]
    for r in results:
        buckets[_bin_index(r["favorite_win_probability"], edges)].append(r)

    bins = []
    for i, bucket in enumerate(buckets):
        bins.append(
            {
                "bin_low": edges[i],
                "bin_high": edges[i + 1],
                "count": len(bucket),
                "mean_predicted_probability": _mean(
                    [r["favorite_win_probability"] for r in bucket]
                ),
                "observed_favorite_win_rate": _mean([r["outcome"] for r in bucket]),
            }
        )
    return bins


def _tour_breakdown(results: list[dict]) -> dict:
    breakdown = {}
    for tour in TOURS:
        subset = [r for r in results if r["tour"] == tour]
        breakdown[tour] = {
            "count": len(subset),
            "brier_score": _brier_score(subset),
            "reliability_bins": _reliability_bins(subset),
        }

    # Fail loud, not silent (code review finding): TOURS is a fixed tuple, so
    # a result whose tour isn't in it would otherwise vanish from every
    # bucket while still counting toward the overall scored_count/brier_score.
    covered = sum(b["count"] for b in breakdown.values())
    if covered != len(results):
        unknown = sorted({r["tour"] for r in results} - set(TOURS))
        raise ValueError(f"Unrecognized tour value(s) not in {TOURS}: {unknown}")

    return breakdown


def _risk_label_breakdown(results: list[dict]) -> dict:
    breakdown = {}
    for label in RISK_LABELS:
        subset = [r for r in results if r["risk_label"] == label]
        breakdown[label] = {
            "count": len(subset),
            "observed_upset_rate": _mean([1 - r["outcome"] for r in subset]),
        }

    # Fail loud, not silent (code review finding): RISK_LABELS mirrors
    # upset_model.py's _determine_risk_label() by hand (see the module
    # comment above); if that model ever adds/renames a label, results
    # carrying it would otherwise vanish from this breakdown with no error.
    covered = sum(b["count"] for b in breakdown.values())
    if covered != len(results):
        unknown = sorted({r["risk_label"] for r in results} - set(RISK_LABELS))
        raise ValueError(f"Unrecognized risk_label value(s) not in {RISK_LABELS}: {unknown}")

    return breakdown


def compute_metrics(results: list[dict]) -> dict:
    """Aggregates scored match results into the full calibration report body."""
    return {
        "scored_count": len(results),
        "brier_score": _brier_score(results),
        "reliability_bins": _reliability_bins(results),
        "by_tour": _tour_breakdown(results),
        "by_risk_label": _risk_label_breakdown(results),
    }
