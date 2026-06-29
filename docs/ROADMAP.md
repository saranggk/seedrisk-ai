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

## Phase 7 — Polish & Documentation (next)

- Improve the README.
- Add `docs/METHODOLOGY.md`.
- Polish UI, loading/error states, copy, and project presentation.

## Optional Later Phases

- SQLite/Postgres/Supabase persistence.
- Logistic regression or XGBoost model upgrade.
- Real ATP/WTA data ingestion.
- Bracket simulator.
- Historical accuracy evaluation.
