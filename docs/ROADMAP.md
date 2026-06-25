# SeedRisk AI — Build Roadmap

This project is built in small, reviewable phases. Each phase is implemented, explained, and tested locally before the next one starts. Status is tracked below.

## Phase 0 — Project Scaffolding ✅

Create the top-level folder structure (`frontend/`, `backend/`, `data/`, `docs/`), the project README, and this roadmap. No app code yet — just the map of what's coming.

## Phase 1 — Seed Data ✅

Create the small local seed dataset of sample Wimbledon-style matches and players as plain JSON in `/data/sample_matches.json` (8 matches, each with a favorite/underdog player pair). Columns include `player_name`, `ranking`, `seed`, `grass_win_pct`, `recent_win_pct`, `wimbledon_win_pct`, `hold_rate_grass`, `break_rate_grass`, `tiebreak_win_pct`, `last_10_record`, `h2h_wins`, `h2h_losses`, documented in `docs/DATA_DICTIONARY.md`. A `backend/app/data/loader.py` utility validates the JSON is parsable and flattens it for inspection. This is the raw material every later phase reads from.

## Phase 2 — Backend Foundation (next)

Stand up the FastAPI app skeleton in `/backend`: project structure, dependency management, SQLite database setup, and a way to load the Phase 1 seed data into it (same match/player shape as `sample_matches.json`, now as SQLite tables). No prediction or scoring logic yet — just a working API server with a health check and data access layer.

## Phase 3 — Matches API

Implement `GET /matches` and `GET /matches/{id}` backed by the seed data in SQLite. This gives the frontend (later) real match data to render, with no model involved yet.

## Phase 4 — Rule-Based Upset Scoring Model

Implement a simple, explainable rule-based scoring model (pandas-based feature engineering) that takes the match stats and outputs `favorite_win_probability`, `upset_probability`, `risk_label`, `top_factors`, and `feature_contributions`. Expose it via `GET /matches/{id}/prediction`.

## Phase 5 — LLM Analyst Layer

Add the Claude-powered analyst report endpoint, `POST /matches/{id}/analysis`. The prompt is strictly constrained to the structured stats and model output already computed in Phase 4 — Claude explains, it does not predict, and it cannot introduce facts not present in the supplied data.

## Phase 6 — Frontend Foundation

Scaffold the Next.js + TypeScript + Tailwind app in `/frontend`. Basic layout, design tokens, and a connection to the backend API. No real dashboard UI yet.

## Phase 7 — Dashboard Page

Build the dashboard page showing match cards: favorite, underdog, rankings, upset probability, risk label, and top 3 upset-risk reasons, pulling from the Phase 3/4 endpoints.

## Phase 8 — Match Detail Page

Build the match detail page: full matchup details, model prediction, feature breakdown, and the AI-generated analyst report from Phase 5.

## Phase 9 — Model Upgrade (Optional/Later)

Upgrade the rule-based model from Phase 4 to a trained model (logistic regression, then optionally XGBoost) using scikit-learn, keeping the same output contract (`favorite_win_probability`, `upset_probability`, `risk_label`, `top_factors`, `feature_contributions`) so nothing downstream needs to change.

## Phase 10 — Polish & Hardening (Optional/Later)

Design polish (confidence badges, hierarchy, Wimbledon-inspired but logo-free styling), error handling, loading states, and groundwork for swapping SQLite for Postgres/Supabase.
