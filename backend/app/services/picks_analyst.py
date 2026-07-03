"""
Picks analyst — grades a user's slate of picks against the model's pre-computed predictions.

Same architectural principle as analyst_generator.py:
- All math (expected correct, contrarian count, slate grade) is computed in
  Python BEFORE Claude is called — Claude cannot change those numbers
- Claude's job is only to write the four prose fields in PicksAnalysisFields
- Falls back to a deterministic mock if ANTHROPIC_API_KEY is not set or fails
"""

import json
import os

from anthropic import Anthropic, APIError

from app.models import Match, PickItem, PicksAnalysisFields, PicksAnalysisResponse, PredictionResponse

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

SYSTEM_PROMPT = """You are a tennis analyst reviewing a user's slate of upset picks against a rule-based statistical model's pre-computed probabilities.

You are NOT the model. All probabilities, risk labels, and computed statistics (expected_correct, contrarian_picks, slate_grade) have already been calculated by a separate system and are supplied to you as facts. Your only job is to write four prose fields characterizing the picks — never change, recompute, or contradict any supplied number or label.

Ground every claim ONLY in the structured data you are given. Do not reference real player injuries, real ATP rankings, or any outside knowledge not present in the supplied data. Tone: concise and direct, like a sports analyst giving a quick pre-match read.

Do not use markdown formatting in any field value — plain prose sentences only."""


def _enrich_picks(
    picks_with_data: list[tuple[PickItem, Match, PredictionResponse]],
) -> tuple[list[dict], dict]:
    """
    Build a structured list Claude can reason over, and compute the aggregate
    stats that go straight into the response (bypassing Claude entirely).
    """
    enriched = []
    expected_correct = 0.0
    upset_count = 0
    contrarian_count = 0

    for item, match, prediction in picks_with_data:
        upset_prob = prediction.upset_probability
        fav_prob = prediction.favorite_win_probability

        if item.choice == "upset":
            expected_correct += upset_prob
            upset_count += 1
            if prediction.risk_label in ("Low", "Medium"):
                contrarian_count += 1
        else:
            expected_correct += fav_prob

        enriched.append({
            "match_id": item.match_id,
            "round": match.round,
            "favorite": match.favorite.player_name,
            "underdog": match.underdog.player_name,
            "risk_label": prediction.risk_label,
            "upset_probability": round(upset_prob, 3),
            "user_pick": item.choice,
            "contrarian": item.choice == "upset" and prediction.risk_label in ("Low", "Medium"),
        })

    total = len(enriched)
    stats = {
        "total_picks": total,
        "upset_picks": upset_count,
        "favorite_picks": total - upset_count,
        "contrarian_picks": contrarian_count,
        "expected_correct": round(expected_correct, 2),
    }
    return enriched, stats


def _grade(stats: dict) -> str:
    total = stats["total_picks"]
    if total == 0:
        return "Balanced"
    upset_pct = stats["upset_picks"] / total
    contrarian_pct = stats["contrarian_picks"] / total
    if upset_pct >= 0.6 or contrarian_pct >= 0.4:
        return "Aggressive"
    if upset_pct <= 0.3:
        return "Conservative"
    return "Balanced"


def _mock_picks_report(enriched: list[dict], stats: dict) -> PicksAnalysisResponse:
    grade = _grade(stats)
    total = stats["total_picks"]
    upset_count = stats["upset_picks"]

    if grade == "Aggressive":
        summary = (
            f"You've picked {upset_count} upset{'s' if upset_count != 1 else ''} out of {total} "
            f"match{'es' if total != 1 else ''} — an aggressive slate that goes against the model "
            "more often than not. If even a couple land, you'll look very smart."
        )
    elif grade == "Conservative":
        summary = (
            f"You've backed the model's favorites in {total - upset_count} of {total} "
            f"match{'es' if total != 1 else ''} — a conservative slate that stays close to "
            "what the model expects. High floor, low ceiling."
        )
    else:
        summary = (
            f"You've split your {total} picks fairly evenly between upsets and favorites — "
            "a balanced approach that mixes model alignment with a few calculated risks."
        )

    upset_picks = [p for p in enriched if p["user_pick"] == "upset"]
    if upset_picks:
        boldest = min(upset_picks, key=lambda p: p["upset_probability"])
        boldest_str = (
            f"{boldest['underdog']} over {boldest['favorite']} "
            f"({boldest['risk_label']} risk, {round(boldest['upset_probability'] * 100)}% model upset probability). "
            "This is your most contrarian call."
        )
    else:
        boldest_str = "You didn't pick any upsets on this slate."

    best = max(
        enriched,
        key=lambda p: p["upset_probability"] if p["user_pick"] == "upset"
        else (1 - p["upset_probability"]),
    )
    if best["user_pick"] == "upset":
        aligned_str = (
            f"{best['underdog']} over {best['favorite']} "
            f"({round(best['upset_probability'] * 100)}% model upset probability) — "
            "the model's numbers are most supportive of an upset here."
        )
    else:
        fav_pct = round((1 - best["upset_probability"]) * 100)
        aligned_str = (
            f"{best['favorite']} over {best['underdog']} "
            f"({fav_pct}% model favorite probability) — "
            "the model most strongly backs your call here."
        )

    return PicksAnalysisResponse(
        slate_grade=grade,
        slate_summary=summary,
        boldest_pick=boldest_str,
        best_aligned_pick=aligned_str,
        portfolio_note=(
            "This is a template summary generated from the model's pre-computed probabilities. "
            "Configure ANTHROPIC_API_KEY for a live AI analysis."
        ),
        picks_count=stats["total_picks"],
        expected_correct=stats["expected_correct"],
        source="mock",
    )


def _claude_picks_report(enriched: list[dict], stats: dict) -> PicksAnalysisResponse:
    grade = _grade(stats)
    payload = {
        "picks": enriched,
        "computed_stats": {**stats, "slate_grade": grade},
    }
    client = Anthropic()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Here is the user's slate of picks with model data and pre-computed stats. "
                    "Write the four analysis prose fields based only on this data:\n\n"
                    + json.dumps(payload, indent=2)
                ),
            }
        ],
        output_format=PicksAnalysisFields,
    )
    fields = response.parsed_output
    if fields is None:
        raise RuntimeError("Claude did not return a parsable picks analysis.")
    return PicksAnalysisResponse(
        **fields.model_dump(),
        slate_grade=grade,
        picks_count=stats["total_picks"],
        expected_correct=stats["expected_correct"],
        source="claude",
    )


def generate_picks_analysis(
    picks_with_data: list[tuple[PickItem, Match, PredictionResponse]],
) -> PicksAnalysisResponse:
    enriched, stats = _enrich_picks(picks_with_data)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return _mock_picks_report(enriched, stats)

    try:
        return _claude_picks_report(enriched, stats)
    except (APIError, RuntimeError):
        return _mock_picks_report(enriched, stats)
