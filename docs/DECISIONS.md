# SeedRisk AI — Decisions

Architectural decisions that shaped SeedRisk AI, in ADR (Architecture Decision Record) format: each entry states the context, the decision, and its consequences. This file is backfilled with decisions already reflected in shipped code; going forward, a new entry is added here each time a future architectural decision actually ships — not written ahead of the work. See `docs/ROADMAP.md` for the forward-looking sequencing plan (real data ingestion, calibration, model upgrades) and `docs/METHODOLOGY.md` for how the shipped system works today.

---

## ADR-1: Rule-based scoring, not a trained ML model

**Context.** The upset-prediction model (`backend/app/services/upset_model.py`, Phase 3) needed a way to turn match stats into a probability. The obvious alternative to hand-written rules was a trained model — logistic regression or a gradient-boosted model.

**Decision.** Score matches with a deterministic, hand-written rule-based function instead of training a model. At the time this shipped, the dataset was 8 sample matches — nowhere near enough to train a model that would generalize. A deterministic function is also fully auditable: every number in the output traces back to a specific rule, which matters doubly because the output is later handed to Claude (ADR-2) to narrate in prose — the numbers need to be trustworthy before a system writes about them.

**Consequences.** The model's weights and thresholds are hand-tuned constants rather than fitted coefficients, so they carry no statistical validation yet. A trained model (logistic regression or XGBoost) remains a planned optional later phase once real ATP/WTA data is available to train on — behind the same output shape (`favorite_win_probability`, `upset_probability`, `risk_label`, `top_factors`, `feature_contributions`), so nothing downstream has to change when that phase lands.

---

## ADR-2: Claude is walled off from ever computing a prediction

**Context.** Once the rule-based model (ADR-1) produces a prediction, the app needed a way to explain that prediction in plain English (Phase 6). The natural risk of using an LLM for this is that it could second-guess or silently alter the underlying numbers.

**Decision.** `favorite_win_probability`, `upset_probability`, `risk_label`, `top_factors`, and `feature_contributions` are all computed by the deterministic model *before* `analyst_generator.py` is ever called. Claude's only job is to turn those already-decided numbers into readable prose — it cannot change them, and the structured output schema (`AnalystReportFields`) doesn't even give it a field where a number could go. Claude is given a closed set of structured facts and instructed to ground every claim in that data only, with no outside knowledge about real players, injuries, or recent results.

**Consequences.** If Claude disagreed with the model's math, there is no way for that disagreement to reach the response — the wall is total and one-directional. This is a deliberate hallucination-reduction measure: the response shape can't drift because Pydantic's structured-output schema constrains it, and the prompt tells Claude to flag data gaps via `confidence_note` rather than invent specifics.

---

## ADR-3: Deterministic mock mode when no API key is set

**Context.** Requiring a live `ANTHROPIC_API_KEY` for local development would block anyone from running the app without first getting a key, and would make the app fail entirely if the Claude call errored (rate limit, network issue).

**Decision.** When `ANTHROPIC_API_KEY` is unset, or the Claude call fails for any reason, `generate_analyst_report()` falls back to a fully deterministic report built directly from the same structured data the live call would have used — so the app works end-to-end either way. The response's `source` field is `"mock"` vs `"claude"` so the frontend can show a demo-mode notice.

**Consequences.** Local development and demos never require an API key. The mock report's prose is hand-written rather than Claude-generated, so it must be kept in sync with the model's factors — the mechanical description of this behavior lives in `docs/METHODOLOGY.md`, alongside a pointer to this entry for the rationale.

---

## ADR-4: Trap Match as its own label, not folded into Medium/High

**Context.** The rule-based model (ADR-1) already produced Low/Medium/High risk buckets from `upset_probability` alone. Some matches have a large ranking gap — making the favorite look completely safe on paper — while the underlying stats still show meaningful upset risk. Under a pure probability-bucket scheme, these matches would just read as "Medium."

**Decision.** Add "Trap Match" as a fourth, narrative-override label — not a higher probability bucket — that fires when the ranking gap is large (≥40) AND `upset_probability` is still elevated (≥30%). That combination is exactly the kind of match an analyst would flag as deceptively dangerous, so it is surfaced as its own label instead of being buried under "Medium."

**Consequences.** "Trap Match" and "Medium" can describe similar underlying probabilities — the label communicates a narrative (safe-looking on paper, riskier underneath), not a higher risk tier. `TRAP_MATCH_MIN_RANKING_GAP` and `TRAP_MATCH_MIN_UPSET_PROBABILITY` are hand-picked thresholds with the same lack-of-statistical-validation caveat as ADR-1's weights.

---

## ADR-5: Sonnet, not Opus, as the default analyst model

**Context.** The Claude analyst layer (ADR-2) needed a default model. Anthropic's model lineup includes higher- and lower-reasoning-tier options at different costs.

**Decision.** Default to `claude-sonnet-4-6`, overridable via the `ANTHROPIC_MODEL` environment variable. The analyst layer is a grounded explanation/writing task over structured data that Claude cannot alter (ADR-2) — not a task that needs Opus-level reasoning — so Sonnet was chosen for cost reasons.

**Consequences.** The model default can be raised (or lowered) per deployment via `ANTHROPIC_MODEL` without a code change. If the analyst layer's job ever expands beyond grounded narration of pre-computed data, this default should be revisited.
