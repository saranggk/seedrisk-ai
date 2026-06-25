# SeedRisk AI

SeedRisk AI is a Wimbledon-focused **upset predictor and match analyst**.

Given a tennis match between a favorite and an underdog, SeedRisk AI:

1. Calculates an **upset probability** and a **risk label** using a stats-driven scoring model (rule-based first, ML later).
2. Hands those structured numbers to an LLM (Claude) whose only job is to **explain** the result in plain English — it never invents stats and never makes the prediction itself.

The goal is a clean, betting-free sports analytics dashboard that surfaces *why* a top seed might be vulnerable on a given day, grounded entirely in real, supplied data.

## Project structure

```
/frontend   Next.js + TypeScript + Tailwind dashboard UI (added in a later phase)
/backend    Python FastAPI service: data, feature engineering, scoring model, LLM analyst endpoint (added in a later phase)
/data       Local seed dataset of sample Wimbledon-style matches and players (added in a later phase)
/docs       Project docs, including the phased build plan (see docs/ROADMAP.md)
```

## Design principles

- The scoring/model layer computes upset probability and risk label. The LLM never does.
- The LLM (Claude) is only allowed to reason over the exact stats it's given — no invented injuries, rankings, head-to-heads, or other facts.
- No gambling language or betting advice anywhere in the product.
- Backend starts on SQLite, structured so Postgres/Supabase can be swapped in later without a rewrite.
