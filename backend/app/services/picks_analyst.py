"""
Picks analyst — grades a user's slate of picks against the model's pre-computed predictions.

Same architectural principle as analyst_generator.py:
- All math (expected correct, contrarian count, slate grade) is computed in
  Python BEFORE Claude is called — Claude cannot change those numbers
- Claude's job is only to write the four prose fields in PicksAnalysisFields
"""

import json
import os

from anthropic import Anthropic, APIError

from app.models import Match, PickItem, PicksAnalysisFields, PicksAnalysisResponse, PredictionResponse


class PicksAnalystServiceUnavailable(RuntimeError):
    """Raised when the Claude picks-analysis call fails; routers turn this into a 502."""


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
    )


def generate_picks_analysis(
    picks_with_data: list[tuple[PickItem, Match, PredictionResponse]],
) -> PicksAnalysisResponse:
    enriched, stats = _enrich_picks(picks_with_data)
    try:
        return _claude_picks_report(enriched, stats)
    except (APIError, RuntimeError) as exc:
        raise PicksAnalystServiceUnavailable("Claude picks analysis failed.") from exc
