# SeedRisk AI — Decisions

Architectural decisions that shaped SeedRisk AI, in ADR (Architecture Decision Record) format: each entry states the context, the decision, and its consequences. This file is backfilled with decisions already reflected in shipped code; going forward, a new entry is added here each time a future architectural decision actually ships — not written ahead of the work. See `docs/ROADMAP.md` for the full phase-by-phase build history and forward-looking sequencing plan, and `docs/METHODOLOGY.md` for how the shipped system works today.

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

---

## ADR-6: One CSS custom-property token layer for color, type, and motion

**Context.** The frontend's portfolio-polish sequence (docs/ROADMAP.md Phase 14) needed to add a dark theme, a richer color vocabulary (neutral surfaces, danger states, accent-contrast text), and a small motion vocabulary — on top of the existing Wimbledon-inspired court-green/purple palette. The naive path for dark mode is scattering Tailwind `dark:` variant classes across every component.

**Decision.** Every meaningful value — color, font role, transition duration/easing — is a CSS custom property in `frontend/app/globals.css`, re-exposed via Tailwind v4's `@theme inline` so components consume generated utility classes (`bg-risk-high`, `font-display`, `duration-standard`) rather than raw Tailwind primitives or literal hex/ms values. Layers build on each other by aliasing rather than duplicating: `--color-risk-*` aliases `--color-court-*` via `var()`, so overriding the base court palette for dark mode repaints both the risk-severity layer and every direct favourite/underdog-identity usage from one block. A dark theme is then a `:root.dark { ... }` override of the same variable names, not a second styling system.

**Consequences.** No component should reach for a raw `zinc-*`/`white`/`black`/`red-*` Tailwind class or a literal color/duration value — if a new value is needed, it becomes a new token in `globals.css` first. This did require one extra token (`--color-on-accent`) discovered mid-implementation: `court-*`/`risk-*` tokens are deliberately *bright* in dark mode for standalone-text legibility, which would make a hardcoded white foreground unreadable wherever those same tokens are used as a solid fill (badges, buttons, panels) — `on-accent` is the dedicated foreground for that specific case, kept separate so the fill tokens don't have to compromise between two different jobs.

---

## ADR-7: Native `<dialog>` for the modal primitive, not a hand-rolled focus trap or a UI-library dependency

**Context.** The one real modal in the app (Pick Mode's "Analysis results") was a plain conditional-render `<div>` with no focus trap, no `role="dialog"`/`aria-modal`, and a close button with no accessible label — the single most-cited gap across the frontend-UI ideation run (docs/ROADMAP.md Phase 14). Fixing it properly meant choosing between hand-rolling a focus trap, adding a headless-UI dependency (e.g. Radix Dialog), or using the browser's native `<dialog>` element.

**Decision.** Build the reusable `Modal` primitive (`frontend/components/Modal.tsx`) on native `<dialog>`, opened via `.showModal()`. The browser provides a correct focus trap, Escape-to-close, and focus-return-to-the-trigger-on-close for free — no hand-rolled trap logic (a common source of subtle accessibility bugs) and no new dependency, consistent with every other UI decision in this codebase (hand-rolled SVG radar chart instead of a charting library, self-hosted fonts instead of a runtime font-loading service, plain emoji instead of an icon library).

**Consequences.** Click-outside-to-close needed its own small technique (checking `event.target === <the dialog element>` in a click handler on the dialog itself, since a click on the native `::backdrop` reports the dialog as its target) rather than the traditional stopPropagation-on-inner-content pattern. This assumes evergreen-browser support for `<dialog>`/`.showModal()` — acceptable for a portfolio project's target audience, revisit if broader browser support ever becomes a requirement.

---

## ADR-8: Calibration data exposed via a new backend endpoint, not a static frontend artifact

**Context.** The batch backtest calibration harness (docs/ROADMAP.md Phase 13) already computes real reliability data and commits it to `data/calibration_report.json`, but that file sits outside both `backend/` and `frontend/` and is not served anywhere. Connecting it to the live product (Phase 14's calibration-aware confidence display) meant deciding how the frontend should get it — a new minimal backend endpoint, or copying/importing the JSON directly into the frontend build.

**Decision.** Add `GET /calibration`, which reads the committed report and returns only its `reliability_bins` (backend/app/routers/calibration.py). This mirrors every other endpoint in the app (`/matches`, `/matches/{id}/prediction`, etc.): the backend is the single owner of all data the frontend displays, and the frontend never reads a file the backend doesn't also serve.

**Consequences.** The Pydantic `CalibrationResponse` model deliberately declares only `reliability_bins` — not `brier_score`, `by_tour`, `by_risk_label`, or `scored_count` — so FastAPI's response serialization enforces that boundary structurally, the same pattern ADR-2 uses to keep Claude out of the model's numbers. If a future feature needs the Brier score or per-tour breakdown, that's a new field on the response model, not a reach into the raw JSON file from the frontend.
