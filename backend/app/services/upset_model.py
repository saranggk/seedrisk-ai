"""
Phase 3 — rule-based upset scoring model.

WHY RULE-BASED (NOT TRAINED ML) FOR NOW:
We only have 8 sample matches — nowhere near enough data to train a model
that would generalize. A deterministic, hand-written scoring function is
fully auditable instead: every number in the output can be traced back to a
specific rule below. That auditability matters doubly here because Phase 6
will hand this model's output to an LLM to explain — we need to trust the
numbers before we trust a system that writes prose about them. A trained
model (logistic regression / XGBoost) is a planned *optional later phase*,
once there's real ATP/WTA data to train on, behind this exact same output
shape (favorite_win_probability, upset_probability, risk_label, top_factors,
feature_contributions) so nothing downstream has to change.

HOW THE SCORE IS BUILT, IN PLAIN TERMS:
1. Start from a BASELINE_UPSET_PROBABILITY. This represents "a generic
   underdog's chance with no other information" — upsets aren't freak
   accidents, they have a real baseline rate, so we don't start at 0.
2. For each factor below (ranking gap, grass form, recent form, etc.), compute
   how much the underdog vs. favorite difference should nudge that baseline
   up (underdog has an edge -> more upset risk) or down (favorite has a clear
   edge -> less upset risk).
3. Sum all those nudges and add them to the baseline.
4. Clamp the result to a believable range — even a huge mismatch on paper
   still has some upset risk, and even a vulnerable favorite is still more
   likely than not to win, so we never let the model claim near-certainty.
5. favorite_win_probability is just 1 - upset_probability (the favorite and
   underdog are the only two outcomes we model here).
"""

from app.models import FeatureContribution, Match, PredictionResponse

# A generic underdog's baseline upset chance, before we look at any stats.
# Tennis upsets are common enough at majors that 0 would be unrealistic.
BASELINE_UPSET_PROBABILITY = 0.20

# However extreme the stats look, we never report a probability outside
# this range — real matches always retain some uncertainty in both directions.
MIN_UPSET_PROBABILITY = 0.05
MAX_UPSET_PROBABILITY = 0.65

# Risk label thresholds, applied to the final (clamped) upset_probability.
# These boundaries are deliberately simple and documented here so they're
# easy to tune later once we have real outcomes to check them against.
RISK_LOW_MAX = 0.20          # upset_probability below this -> "Low"
RISK_MEDIUM_MAX = 0.35       # below this (and above RISK_LOW_MAX) -> "Medium"
# Anything at or above RISK_MEDIUM_MAX -> "High" (unless it's a Trap Match, below)

# A "Trap Match" is a specific narrative, not just a probability bucket: the
# ranking gap makes the favorite look completely safe on paper, but the
# underlying stats still show meaningful upset risk. That combination is
# exactly the kind of match an analyst would flag as deceptively dangerous,
# so we surface it as its own label instead of burying it under "Medium".
TRAP_MATCH_MIN_RANKING_GAP = 40
TRAP_MATCH_MIN_UPSET_PROBABILITY = 0.30


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _scaled_impact(diff: float, weight: float, cap: float) -> float:
    """
    Turn a raw stat difference into a bounded probability nudge.

    `diff` is (underdog_value - favorite_value): positive means the underdog
    has the edge on this stat. Multiplying by `weight` converts that into a
    probability-scale nudge, and `cap` stops any single factor from
    dominating the whole score, no matter how large the raw difference is.
    """
    return _clamp(diff * weight, -cap, cap)


def _direction(impact: float) -> str:
    # A factor with zero impact (e.g. an even head-to-head record) didn't
    # push the score in either direction, so it shouldn't be mislabeled as
    # "increases" just because 0 >= 0 — it gets its own neutral label.
    if impact == 0:
        return "neutral"
    return "increases_upset_risk" if impact > 0 else "decreases_upset_risk"


def _score_ranking_gap(match: Match) -> FeatureContribution:
    # Lower ranking number = better. In essentially every match here the
    # favorite has the lower (better) ranking, so this gap is usually
    # positive. A LARGE gap means the favorite is clearly the better player
    # by ranking, which should REDUCE upset risk. A SMALL gap means rankings
    # don't offer much protection, so we barely adjust the baseline at all.
    gap = match.underdog.ranking - match.favorite.ranking
    cap = 0.10
    impact = -_scaled_impact(gap / 100, weight=0.06, cap=cap)
    # Note the extra minus sign: a positive gap (favorite better ranked)
    # must produce a NEGATIVE impact (less upset risk), so we flip the sign
    # rather than reusing _scaled_impact's sign convention directly.
    reason = (
        f"Ranking gap of {gap} places ({match.favorite.player_name} #{match.favorite.ranking} "
        f"vs {match.underdog.player_name} #{match.underdog.ranking}) "
        f"{'gives the favorite real protection' if impact < 0 else 'offers little protection to the favorite'}."
    )
    return FeatureContribution(
        feature="ranking_gap",
        label="Ranking gap",
        impact=round(impact, 4),
        max_impact=cap,
        direction=_direction(impact),
        reason=reason,
    )


def _score_pct_diff(
    match: Match, feature: str, label: str, weight: float, cap: float, context: str
) -> FeatureContribution:
    """Shared scorer for the simple "underdog_pct - favorite_pct" style stats."""
    favorite_value = getattr(match.favorite, feature)
    underdog_value = getattr(match.underdog, feature)
    diff = underdog_value - favorite_value
    impact = _scaled_impact(diff, weight=weight, cap=cap)

    diff_points = round(abs(diff) * 100)
    if diff >= 0:
        reason = f"Underdog has a {diff_points}-point {context} advantage."
    else:
        reason = f"Favorite has a {diff_points}-point {context} advantage."

    return FeatureContribution(
        feature=feature,
        label=label,
        impact=round(impact, 4),
        max_impact=cap,
        direction=_direction(impact),
        reason=reason,
    )


def _score_h2h(match: Match) -> FeatureContribution:
    # Head-to-head is read from the underdog's side: wins minus losses
    # against this specific opponent. A positive net record means the
    # underdog has actually beaten this favorite before, which is a strong,
    # concrete signal independent of general form or ranking.
    net = match.underdog.h2h_wins - match.underdog.h2h_losses
    net = _clamp(net, -3, 3)  # a handful of meetings is already a strong signal
    cap = 0.09
    impact = _scaled_impact(net, weight=0.03, cap=cap)

    if net > 0:
        reason = (
            f"{match.underdog.player_name} leads the head-to-head "
            f"{match.underdog.h2h_wins}-{match.underdog.h2h_losses}."
        )
    elif net < 0:
        reason = (
            f"{match.favorite.player_name} leads the head-to-head "
            f"{match.favorite.h2h_wins}-{match.favorite.h2h_losses}."
        )
    else:
        reason = "Head-to-head record is even."

    return FeatureContribution(
        feature="h2h_edge",
        label="Head-to-head edge",
        impact=round(impact, 4),
        max_impact=cap,
        direction=_direction(impact),
        reason=reason,
    )


def _build_feature_contributions(match: Match) -> list[FeatureContribution]:
    return [
        _score_ranking_gap(match),
        _score_pct_diff(
            match, "surface_win_pct", "Grass win percentage",
            weight=0.5, cap=0.08, context="grass win percentage",
        ),
        _score_pct_diff(
            match, "recent_win_pct", "Recent form",
            weight=0.4, cap=0.07, context="recent win percentage",
        ),
        _score_pct_diff(
            match, "tournament_win_pct", "Wimbledon win percentage",
            weight=0.3, cap=0.06, context="Wimbledon win percentage",
        ),
        _score_pct_diff(
            match, "surface_hold_rate", "Grass service hold rate",
            weight=0.3, cap=0.06, context="grass hold rate",
        ),
        _score_pct_diff(
            match, "surface_break_rate", "Grass break rate",
            weight=0.35, cap=0.07, context="grass break rate",
        ),
        _score_pct_diff(
            match, "tiebreak_win_pct", "Tiebreak win percentage",
            weight=0.25, cap=0.05, context="tiebreak win percentage",
        ),
        _score_h2h(match),
    ]


def _determine_risk_label(upset_probability: float, ranking_gap: int) -> str:
    # Trap Match check comes first: it's a narrative override, not just
    # another probability bucket. A big ranking gap normally reads as "safe
    # favorite," so if upset_probability is still meaningfully elevated
    # despite that gap, it deserves a distinct label rather than "Medium."
    if (
        ranking_gap >= TRAP_MATCH_MIN_RANKING_GAP
        and upset_probability >= TRAP_MATCH_MIN_UPSET_PROBABILITY
    ):
        return "Trap Match"
    if upset_probability < RISK_LOW_MAX:
        return "Low"
    if upset_probability < RISK_MEDIUM_MAX:
        return "Medium"
    return "High"


def _build_top_factors(contributions: list[FeatureContribution]) -> list[str]:
    # These are the top MODEL FACTORS — the largest prediction drivers by
    # absolute impact, regardless of direction. Some of them increase upset
    # risk, but others (e.g. a ranking gap that protects the favorite)
    # decrease it. "top_factors" should not be read as "top upset reasons."
    ranked = sorted(contributions, key=lambda c: abs(c.impact), reverse=True)
    return [c.reason for c in ranked[:3]]


def predict_upset(match: Match) -> PredictionResponse:
    """Run the rule-based model on a single match and return the full prediction."""
    contributions = _build_feature_contributions(match)

    raw_adjustment = sum(c.impact for c in contributions)
    upset_probability = _clamp(
        BASELINE_UPSET_PROBABILITY + raw_adjustment,
        MIN_UPSET_PROBABILITY,
        MAX_UPSET_PROBABILITY,
    )
    favorite_win_probability = 1 - upset_probability

    ranking_gap = match.underdog.ranking - match.favorite.ranking
    risk_label = _determine_risk_label(upset_probability, ranking_gap)
    top_factors = _build_top_factors(contributions)

    return PredictionResponse(
        match_id=match.match_id,
        favorite_name=match.favorite.player_name,
        underdog_name=match.underdog.player_name,
        favorite_win_probability=round(favorite_win_probability, 4),
        upset_probability=round(upset_probability, 4),
        risk_label=risk_label,
        top_factors=top_factors,
        feature_contributions=contributions,
    )
