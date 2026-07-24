---
title: Free-tier deployment for a split Python/Next.js monorepo (Render + Vercel)
date: 2026-07-24
category: tooling-decisions
module: deployment
problem_type: tooling_decision
component: tooling
severity: medium
applies_when:
  - "Deploying a FastAPI + Next.js split-repo app to free-tier hosting (Render + Vercel)"
  - "Wiring CORS between a deployed frontend origin and a deployed backend without hardcoding URLs into source"
  - "Choosing between committing deploy config as code (render.yaml Blueprint) vs manual dashboard setup"
  - "Accepting cold-start tradeoffs on Render's free tier for a $0 portfolio deployment"
related_components: [development_workflow, documentation]
tags: [deployment, render, vercel, cors, free-tier, env-vars, fastapi, nextjs]
---

# Free-tier deployment for a split Python/Next.js monorepo (Render + Vercel)

## Context

SeedRisk is a portfolio project — it needed a live, shareable URL rather than only running locally. The constraint was zero budget (free tier only), and the codebase is a monorepo split across two runtimes that don't share a single deploy target: a Python/FastAPI backend (`backend/`) and a Node/Next.js frontend (`frontend/`). That split meant two separate hosting providers, deployed and configured independently, needed to be wired together. Deployment had been an acknowledged gap for a while — named explicitly as one of the project's biggest pain points in an earlier session — but stayed unaddressed until this session.

## Guidance

The practice for deploying a monorepo with a Python backend + Next.js frontend to two separate free-tier hosts:

- **Backend (Render):** a `render.yaml` Blueprint at the repo root (`render.yaml:1-16`) lets Render auto-detect and create the service from a versioned file instead of manual dashboard clicking. `rootDir: backend` (`render.yaml:6`) points Render at the backend subdirectory in the monorepo. `healthCheckPath: /health` (`render.yaml:9`) gives Render a real liveness check backed by the app's actual `/health` endpoint (`backend/app/main.py:56-59`) instead of just probing `/`. Secrets (`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `ALLOWED_ORIGINS`) are declared with `sync: false` (`render.yaml:10-16`) so they show up as fields to fill in on the Render dashboard's Environment tab but are never committed to the repo.
- **Frontend (Vercel):** Vercel's project import already supports picking a subdirectory as "Root Directory" for monorepos — no extra config file needed for a standard Next.js app. The only thing to set is the `NEXT_PUBLIC_API_BASE_URL` env var pointing at the deployed backend; the frontend code that reads it (`frontend/lib/api.ts:19-20`) already existed before this deployment work — it's not something this change added, just something this change finally gave a non-localhost value.
- **CORS is the connective tissue** between two independently-deployed services with unpredictable URLs — Render and Vercel both assign generated subdomains (`*.onrender.com`, `*.vercel.app`) unless you attach a custom domain. Hardcoding the production origin into source would mean a code change and a redeploy every time the origin changes (e.g. if the Vercel project is ever recreated). Instead, `ALLOWED_ORIGINS` is an env-var-driven allowlist: comma-separated, parsed and *appended* to the existing hardcoded local-dev origins rather than replacing them (`backend/app/main.py:40-50`), so the origin can be added or changed from the Render dashboard alone, no code touched.
- **Deploy order matters and looks circular but isn't**: backend first, since its URL is needed for the frontend's `NEXT_PUBLIC_API_BASE_URL`; then frontend, since its URL is needed for the backend's `ALLOWED_ORIGINS`. The backend needs one final redeploy/restart after the frontend exists, to pick up the frontend's URL and stop blocking its requests (README.md "Deployment" section, "Close the loop" step).

## Why This Matters

Without the `ALLOWED_ORIGINS` env var pattern, adding a deployed frontend's origin would require hardcoding the Vercel URL directly into `backend/app/main.py` and shipping a new commit + redeploy every time that origin changes — turning what should be a config change into a code change. The `render.yaml` Blueprint also makes the deployment reproducible: a fresh Render account can recreate the exact same service (build command, start command, health check, root dir) by reading one versioned file, rather than the setup living only as manually-clicked dashboard state that's lost if the service ever needs to be recreated.

## When to Apply

- Deploying a monorepo where the backend and frontend go to different hosting providers (e.g. Render + Vercel, Fly.io + Netlify).
- Any time a deployed service's allowed CORS origins can't be known until the *other* service is deployed — a circular-feeling dependency. Solve it with an env var plus one final restart, not by trying to predict the URL in advance or hardcoding a guess.
- Free-tier hosting for a portfolio/demo project specifically: call out the tradeoff explicitly rather than engineering around it. The README states the Render free tier spins down after 15 minutes of idle, so the first request after a lull takes 30-60s to wake up — expected and accepted for a $0 portfolio deploy. Eliminating that cold start (a paid tier, or a keep-alive ping that likely violates the free tier's fair-use terms) isn't worth it for a demo project's actual traffic pattern.

## Examples

`render.yaml` env var declaration — fields to fill in on the dashboard, never committed as values:

```yaml
envVars:
  - key: ANTHROPIC_API_KEY
    sync: false
  - key: ALLOWED_ORIGINS
    sync: false
```

`ALLOWED_ORIGINS` parsing and merge in `backend/app/main.py:40-50` — appended to, not replacing, the local-dev origins:

```python
_extra_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", *_extra_origins],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Deploy-order steps from the README's Deployment section: Render Blueprint first → note its `.onrender.com` URL → Vercel import with `NEXT_PUBLIC_API_BASE_URL` set to that URL → note the resulting `.vercel.app` URL → back to Render to set `ALLOWED_ORIGINS` to the Vercel URL and redeploy.

## Related

- No related `docs/solutions/` entries — the only other entry (`docs/solutions/architecture-patterns/remove-mock-fallback-fail-fast-llm-integration.md`, also from this session) is a distinct topic (fail-fast error handling for the Claude API integration, not infra/CORS config); confirmed no meaningful overlap.
- No related GitHub issues found.
