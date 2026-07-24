# SeedRisk AI — Build Roadmap

This project is built in small, reviewable phases. Each phase is implemented, explained, and tested locally before the next one starts.

## Phase 0 — Project Scaffolding ✅

Folder structure (`frontend/`, `backend/`, `data/`, `docs/`), project README, this roadmap.

## Phase 1 — Seed Data ✅

Sample Wimbledon dataset (`data/sample_matches.json`, 8 matches), `docs/DATA_DICTIONARY.md`, and a loader utility (`backend/app/data/loader.py`).

## Phase 2 — Backend Foundation ✅

FastAPI backend with `GET /health`, `GET /matches`, `GET /matches/{id}`. Pydantic models for `Player`/`Match`/`MatchResponse`. In-memory JSON data, 404 handling. No DB, no prediction logic, no LLM.

## Phase 3 — Rule-Based Upset Scoring Model ✅

`backend/app/services/upset_model.py` — explainable rule-based scoring. Added `GET /matches/{id}/prediction`, returning `favorite_win_probability`, `upset_probability`, `risk_label` (Low/Medium/High/Trap Match), `top_factors`, and `feature_contributions`. No LLM, no frontend yet.

## Phase 4 — Frontend Dashboard ✅

Next.js + TypeScript + Tailwind frontend under `/frontend`. API client (`lib/api.ts`) and types (`lib/types.ts`). Dashboard fetches matches + predictions and renders a card per match (risk badge, probabilities, top factors), with loading and error states. Added CORS to the backend so the browser can reach it.

## Phase 5 — Match Detail Page ✅

Dynamic route `/matches/[matchId]`. Cards on the dashboard now link to their detail page. Detail page adds a full favorite-vs-underdog stat comparison and every `feature_contribution` with signed impact and a proportional bar. Distinct `MatchNotFound` state for bad IDs vs a generic error state for a down backend.

## Phase 6 — Claude Analyst Layer ✅

`backend/app/services/analyst_generator.py` and `POST /matches/{id}/analysis` — Claude (`claude-sonnet-4-6` by default, overridable via `ANTHROPIC_MODEL`) explains the existing prediction in 7 structured fields (`AnalystReportFields`), constrained so it can't carry a probability or label of its own. Grounded strictly in the supplied match/prediction data, no betting language. Falls back to a deterministic mock report (`source: "mock"`) if no API key or the call fails, so the app always works. Frontend adds an on-demand "Generate analyst report" section with a demo-mode notice in mock mode. Verified with both mock mode and a real `ANTHROPIC_API_KEY` (`source: "claude"` confirmed).

## Phase 7 — Portfolio Polish & Documentation ✅

Wimbledon-inspired design applied to all real app pages. Dashboard gets a dark green header banner and a summary strip (total matches, High Risk count, Trap Match count, average upset %). Match cards updated with risk-coloured left border accent, probability bars (green for favourite win, purple for upset), High/Trap Match card tints, and cleaner player hierarchy. Risk badges switched to outlined pill style with correct colour roles (green/amber/strawberry red/purple). Player comparison table reordered to favourite-left | stat-centre | underdog-right. Feature contribution bars updated to purple for `increases_upset_risk` and green for `decreases_upset_risk`. Analyst report section polished with dark green "Final Take" panel, rose/blush demo-mode notice, and an italic confidence note. Match detail page restructured as a premium match briefing card. Loading, error, and not-found states improved. Root `README.md` rewritten with full setup, demo flow, and project overview. `docs/METHODOLOGY.md` added explaining the model, risk labels, Claude's role, and data limitations.

## Phase 8 — Dashboard Controls & Data Expansion ✅

Sample dataset doubled from 8 to 16 matches (M001–M016), engineered to produce a balanced distribution across all four risk labels (6 Low, 3 Medium, 3 High, 4 Trap Match). Dashboard gains filter tabs (by risk label, colour-matched to risk badges), a sort toggle (upset % ascending/descending/none), a search bar (player name substring match), and a "Showing X of Y" counter. All three controls compose — filter, search, and sort can be active simultaneously. The SummaryStrip continues to reflect the full unfiltered dataset so aggregate stats stay stable while browsing.

## Phase 9 — Picks Mode ✅

`backend/app/services/picks_analyst.py` and `POST /picks/analysis` — the user calls Favourite or Upset on each dashboard card ("Pick Mode"), and the backend grades the whole slate (`slate_grade`: Aggressive/Balanced/Conservative, `expected_correct`), computed in Python before Claude (or the mock) writes the portfolio-level prose. Same non-negotiable split as the analyst layer: Claude cannot alter the grade or the count.

## Phase 10 — Regression Test Hardening ✅

Golden-file snapshot tests for `predict_upset()` (`backend/tests/test_upset_model_snapshot.py`) so a future weight/threshold edit can't silently change model output, plus a schema contract test (`backend/tests/test_model_contracts.py`) asserting Claude's response schemas are structurally incapable of carrying a probability or risk label of their own (enforces ADR-2 as code, not just prompt instructions).

## Phase 11 — Surface-Agnostic Schema Refactor ✅

`Player`'s grass-specific field names (e.g. `grass_win_pct`) renamed to generic `surface_*` names, and `favorite`/`underdog` are now derived from ranking/seed at load time (`backend/app/data/loader.py`) rather than trusted as stored labels in the JSON — groundwork for supporting non-grass tournaments later without a schema change.

## Phase 12 — Real Wimbledon Backtest Data Pipeline ✅

`backend/scripts/wimbledon_backtest/` fetches, cleans, and engineers real ATP/WTA Wimbledon match data (2021–2025, via an archival mirror of Jeff Sackmann's `tennis_atp`/`tennis_wta` datasets — CC BY-NC-SA 4.0) into `data/wimbledon_backtest_matches.json`. Offline only — this real dataset does not power the live dashboard (which still runs on the synthetic `data/sample_matches.json`); it exists so the model can be checked against real outcomes (Phase 13).

## Phase 13 — Backtest Calibration Harness ✅

`backend/scripts/backtest_calibration/` scores every scoreable match from Phase 12's real dataset against the live `predict_upset()` model and computes an overall Brier score plus reliability bins (grouped in 0.05-wide predicted-probability buckets, with breakdowns by tour and by risk label), committed to `data/calibration_report.json`. Diagnostic only at this point — not yet connected to the live app (see Phase 14).

## Phase 14 — Frontend Portfolio Polish Sequence ✅

Ran `/ce-ideate` focused on frontend/UI, producing a 7-idea ranked list (`docs/ideation/2026-07-21-frontend-ui-ideation.html`); 6 were built end-to-end (one, URL-synced browsing state, deliberately deprioritized as sound-but-undistinctive):

- **Typography & color tokens** — `--color-risk-*`/`--color-court-*` CSS custom properties as the single override point for risk/identity color everywhere; self-hosted Fraunces/Work Sans/JetBrains Mono via `next/font/local`.
- **Zero-anchored prediction visualization** — `max_impact` exposed per feature so bars scale consistently across matches; `EngineEvalBar` (one continuous, always-sums-to-100% split bar) replacing two separately-scaled bars; a hand-rolled SVG `PlayerRadarChart`.
- **Dark "Night Session" theme** — extends the token layer with neutral (`surface`/`text-*`/`border`) and `on-accent` tokens, toggled via a persisted `<html class="dark">` override with a `prefers-color-scheme` fallback.
- **One motion system, one signature moment** — a small `duration`/`easing` vocabulary applied app-wide via Tailwind v4's own `--default-transition-duration` override; a shared `Spinner`; `EngineEvalBar` rallies (brief overshoot, then settles) into place on mount, respecting `prefers-reduced-motion`.
- **Accessible modal & pick controls** — a reusable `Modal` primitive on the native `<dialog>` element (focus trap, Escape-to-close, and focus-return all native, zero new dependencies), `aria-pressed` on pick buttons, `aria-live` on the picks counter.
- **Calibration-aware confidence display** — `GET /calibration` connects Phase 13's harness to the live app for the first time; each prediction is bucketed ("Likely"/"Toss-up"/"Underdog Alert", reusing the existing risk-label thresholds) and annotated with the real observed accuracy at that confidence level, gated on a minimum sample size so thin historical bins aren't quoted as if they were meaningful.

## Optional Later Phases

- Real ATP/WTA data ingestion for the *live* dashboard, not just the offline calibration check (Phase 12 built the offline pipeline; the live app still runs on synthetic sample data).
- Deployment (Fly.io, Vercel + Railway, etc.).
- SQLite/Postgres/Supabase persistence.
- Logistic regression or XGBoost model upgrade, trained on the real data from Phase 12.
- Full bracket simulator with round-by-round progression.
