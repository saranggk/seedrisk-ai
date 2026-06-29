# SeedRisk AI

SeedRisk AI is a Wimbledon-focused **upset predictor and match analyst**.

Given a tennis match between a favorite and an underdog, SeedRisk AI:

1. Calculates an **upset probability** and a **risk label** using a stats-driven scoring model (rule-based first, ML later).
2. Hands those structured numbers to an LLM (Claude) whose only job is to **explain** the result in plain English — it never invents stats and never makes the prediction itself.

The goal is a clean, betting-free sports analytics dashboard that surfaces *why* a top seed might be vulnerable on a given day, grounded entirely in real, supplied data.

## Project structure

```
/frontend   Next.js + TypeScript + Tailwind dashboard UI
/backend    Python FastAPI service — match data, rule-based upset scoring model (LLM analyst endpoint comes later)
/data       Local seed dataset of sample Wimbledon-style matches and players
/docs       Project docs, including the phased build plan (see docs/ROADMAP.md)
```

The backend currently serves data straight from `/data/sample_matches.json`
(no database) and exposes:

- `GET /health`
- `GET /matches`
- `GET /matches/{id}`
- `GET /matches/{id}/prediction` — rule-based upset probability, risk label, and feature breakdown

The frontend dashboard fetches matches and predictions from the backend and
renders them as cards with risk badges (Low / Medium / High / Trap Match) and
top model factors. It needs the backend running to show any data.

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md)
for setup/run instructions, and [docs/ROADMAP.md](docs/ROADMAP.md) for current build status.

## Design principles

- The scoring/model layer computes upset probability and risk label. The LLM never does.
- The LLM (Claude) is only allowed to reason over the exact stats it's given — no invented injuries, rankings, head-to-heads, or other facts.
- No gambling language or betting advice anywhere in the product.
- The model starts rule-based (fully auditable, no training data needed) and can be upgraded to a trained model later behind the same output shape. Likewise, persistence starts as a flat JSON file and SQLite/Postgres/Supabase is an optional later upgrade, not a current dependency.
