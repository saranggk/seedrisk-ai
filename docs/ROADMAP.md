# SeedRisk AI — Build Roadmap

This project is built in small, reviewable phases. Each phase is implemented, explained, and tested locally before the next one starts.

## Phase 0 — Project Scaffolding ✅

- Top-level folder structure (`frontend/`, `backend/`, `data/`, `docs/`).
- Project README.
- This roadmap.

## Phase 1 — Seed Data ✅

- Local Wimbledon-style JSON dataset (`data/sample_matches.json`, 8 matches, each with a favorite/underdog pair).
- Data dictionary (`docs/DATA_DICTIONARY.md`) explaining every field.
- Data loader utility (`backend/app/data/loader.py`) to validate and inspect the dataset.

## Phase 2 — Backend Foundation ✅

- FastAPI backend under `/backend`.
- `GET /health`.
- `GET /matches`.
- `GET /matches/{id}`.
- Pydantic models for `Player`, `Match`, and `MatchResponse`.
- JSON-backed data loading from the Phase 1 dataset (in-memory, no database).
- 404 handling for missing matches.
- No database, no prediction logic, no LLM.

## Phase 3 — Rule-Based Upset Scoring Model ✅

- Implemented `backend/app/services/upset_model.py` with explainable, documented rule-based logic.
- Added `GET /matches/{id}/prediction`.
- Returns `favorite_win_probability`, `upset_probability`, `risk_label`, `top_factors` (top model factors — largest prediction drivers by absolute impact, not only upset-risk reasons), and `feature_contributions`.
- Risk labels (`Low`, `Medium`, `High`, `Trap Match`) verified to all occur across the sample dataset.
- `feature_contributions[].direction` is `"increases_upset_risk"`, `"decreases_upset_risk"`, or `"neutral"` (when `impact == 0`).
- No LLM and no frontend yet.

## Phase 4 — Frontend Dashboard (next)

- Scaffold the Next.js + TypeScript + Tailwind frontend.
- Build a dashboard showing match cards, upset probabilities, risk labels, and top reasons.
- Pull real data from the FastAPI backend.

## Phase 5 — Match Detail Page

- Add a dynamic match detail route.
- Show full matchup details, prediction summary, player comparison, and feature contributions.
- Make the model explanation visually clear.

## Phase 6 — Claude Analyst Layer

- Add `POST /matches/{id}/analysis`.
- Claude explains the model output using only supplied structured data.
- Claude does not make predictions.
- Add fallback mock analysis if `ANTHROPIC_API_KEY` is missing.

## Phase 7 — Polish & Documentation

- Improve the README.
- Add `docs/METHODOLOGY.md`.
- Polish UI, loading/error states, copy, and project presentation.

## Optional Later Phases

- SQLite/Postgres/Supabase persistence.
- Logistic regression or XGBoost model upgrade.
- Real ATP/WTA data ingestion.
- Bracket simulator.
- Historical accuracy evaluation.
