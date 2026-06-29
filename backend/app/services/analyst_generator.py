"""
Phase 6 — Claude analyst layer.

WHY CLAUDE DOES NOT PREDICT:
favorite_win_probability, upset_probability, risk_label, top_factors, and
feature_contributions are all already computed by the deterministic rule-based
model in app/services/upset_model.py *before* this module is ever called.
Claude's only job here is to turn those already-decided numbers into readable
prose — it cannot change them, and the structured output schema below doesn't
even give it a field where a number could go. If Claude disagreed with the
model's math, there's no way for that disagreement to reach the response.

WHY THIS REDUCES HALLUCINATION RISK:
1. Claude is given a closed set of structured facts (the match, both players'
   stats, the prediction, top_factors, feature_contributions) and explicitly
   instructed to ground every claim in that data only — no outside knowledge
   about real players, injuries, or recent results is requested or wanted.
2. The response is constrained by Pydantic's structured-output schema
   (AnalystReportFields), so the *shape* of the answer can't drift — there's
   no way for Claude to add a field for "his coach said..." because no such
   field exists in the schema.
3. The prompt explicitly tells Claude to use confidence_note to flag gaps
   rather than fill them in with invented specifics.

WHY MOCK MODE EXISTS:
Local development shouldn't require an API key. With no ANTHROPIC_API_KEY
set (or if the Claude call fails for any reason — rate limit, network, etc.),
generate_analyst_report() falls back to a fully deterministic report built
directly from the same structured data, so the app still works end-to-end.
"""

import json
import os

from anthropic import Anthropic, APIError

from app.models import AnalystReportFields, AnalystReportResponse, Match, PredictionResponse

# Overridable via ANTHROPIC_MODEL (see backend/.env.example) — this is a
# grounded explanation/writing task over structured data, not a task that
# needs Opus-level reasoning, so Sonnet is the default for cost reasons.
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

SYSTEM_PROMPT = """You are a tennis analyst explaining a rule-based upset-risk model's output to an informed tennis fan.

You are NOT the model. The upset probability, risk label, and feature contributions you are given have already been calculated by a separate rule-based scoring system. Your only job is to explain that output in clear prose — never change, recompute, second-guess, or contradict any of the supplied numbers or labels.

Ground every claim ONLY in the structured data you are given: the match info, both players' stats, the prediction, top_factors, and feature_contributions. Do NOT invent or assume any fact not present in that data — this includes injuries, rankings, seeds, surfaces, head-to-head results, or recent matches beyond what is explicitly supplied. If the supplied data is insufficient to support a claim you would otherwise want to make, leave the claim out and note the limitation in confidence_note instead of guessing.

Tone: a knowledgeable tennis analyst talking to an informed fan — clear and specific, not hype. Do not use betting language or give betting advice (no odds, no "bet on," no "lock," no stake or wager suggestions). Make clear this is an explanation of a statistical model's estimate, not a guarantee of the outcome.

Do not use markdown formatting (no **, #, bullet characters, etc.) in any field value — plain prose sentences only, including each item in upset_recipe."""


def _build_payload(match: Match, prediction: PredictionResponse) -> dict:
    """
    The exact structured facts Claude is allowed to reason over: match info,
    both players' stats, the prediction, top_factors, and feature_contributions.
    Nothing outside this dict reaches the model.
    """
    return {
        "match": {"match_id": match.match_id, "round": match.round},
        "favorite": match.favorite.model_dump(),
        "underdog": match.underdog.model_dump(),
        "prediction": {
            "favorite_win_probability": prediction.favorite_win_probability,
            "upset_probability": prediction.upset_probability,
            "risk_label": prediction.risk_label,
        },
        "top_factors": prediction.top_factors,
        "feature_contributions": [fc.model_dump() for fc in prediction.feature_contributions],
    }


def _factors_by_direction(prediction: PredictionResponse, direction: str) -> list[str]:
    return [fc.reason for fc in prediction.feature_contributions if fc.direction == direction]


def _mock_report(match: Match, prediction: PredictionResponse) -> AnalystReportResponse:
    """
    Deterministic, template-based report built directly from the rule-based
    model's own output — no LLM call. Used when ANTHROPIC_API_KEY isn't set,
    or as a fallback if the Claude call fails for any reason.
    """
    favorite_name = match.favorite.player_name
    underdog_name = match.underdog.player_name
    protecting = _factors_by_direction(prediction, "decreases_upset_risk")
    threatening = _factors_by_direction(prediction, "increases_upset_risk")
    top_impact = max(prediction.feature_contributions, key=lambda fc: abs(fc.impact))

    match_summary = (
        f"{favorite_name} is favored over {underdog_name} in this {match.round} matchup. "
        f"The model gives {favorite_name} a {round(prediction.favorite_win_probability * 100)}% "
        f"chance to win, putting this match at {prediction.risk_label} upset risk."
    )
    why_favorite_is_favored = (
        " ".join(protecting[:2])
        if protecting
        else f"{favorite_name} doesn't hold a clear statistical edge on the stats supplied here, "
        f"which is part of why this match is rated {prediction.risk_label}."
    )
    why_upset_could_happen = (
        " ".join(threatening[:2])
        if threatening
        else f"No individual stat strongly favors {underdog_name} here — the upset probability "
        "is close to the model's baseline rate for an underdog with no other information."
    )
    upset_recipe = (
        threatening[:3]
        if threatening
        else [
            f"No single supplied stat stands out in {underdog_name}'s favor; an upset would "
            f"likely require {underdog_name} to simply outplay the baseline across the board."
        ]
    )
    final_take = (
        f"This is a {prediction.risk_label} risk match by the model's estimate — {favorite_name} "
        f"is the expected winner, but {underdog_name} is not without a path, as outlined above."
    )
    confidence_note = (
        "This is a deterministic summary generated directly from the rule-based model's output, "
        "not a live AI commentary, because ANTHROPIC_API_KEY is not configured (or the Claude "
        "request failed). It reflects only the stats shown above — not betting advice or a "
        "guaranteed outcome."
    )

    return AnalystReportResponse(
        match_summary=match_summary,
        why_favorite_is_favored=why_favorite_is_favored,
        why_upset_could_happen=why_upset_could_happen,
        key_stat_to_watch=top_impact.reason,
        upset_recipe=upset_recipe,
        final_take=final_take,
        confidence_note=confidence_note,
        source="mock",
    )


def _claude_report(payload: dict) -> AnalystReportResponse:
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    response = client.messages.parse(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Here is the structured match and prediction data. Write the analyst "
                    "report fields based only on this data:\n\n" + json.dumps(payload, indent=2)
                ),
            }
        ],
        output_format=AnalystReportFields,
    )
    fields = response.parsed_output
    if fields is None:
        raise RuntimeError("Claude did not return a parsable structured analyst report.")
    return AnalystReportResponse(**fields.model_dump(), source="claude")


def generate_analyst_report(match: Match, prediction: PredictionResponse) -> AnalystReportResponse:
    """
    Build the structured payload, then use Claude if ANTHROPIC_API_KEY is set
    (falling back to the mock report on any API failure), or go straight to
    the mock report if no key is configured at all.
    """
    payload = _build_payload(match, prediction)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return _mock_report(match, prediction)

    try:
        return _claude_report(payload)
    except (APIError, RuntimeError):
        return _mock_report(match, prediction)
