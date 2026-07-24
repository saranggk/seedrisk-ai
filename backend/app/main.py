"""
SeedRisk AI backend entrypoint.

Run with: uvicorn app.main:app --reload  (from the backend/ directory)
"""

import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Reads backend/.env (if present) into the environment, e.g. ANTHROPIC_API_KEY.
load_dotenv()

# The Claude analyst layer (POST /matches/{id}/analysis, POST /picks/analysis)
# has no mock fallback — without a key those endpoints would 502 on every
# request, so fail loudly at startup instead of at first request.
if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ANTHROPIC_API_KEY is not set. Copy backend/.env.example to backend/.env and add a key.")

from app.routers import calibration, matches

app = FastAPI(
    title="SeedRisk AI API",
    description="Wimbledon-focused upset predictor and match analyst — backend API.",
    version="0.1.0",
)

# Browsers block cross-origin fetches by default. curl/Postman never hit this
# because the same-origin check only applies inside a browser — but the
# Phase 4 Next.js dev server (localhost:3000) calling this API (localhost:8000)
# is a different origin, so without this the dashboard's fetches would fail
# silently with a CORS error in the browser console.
#
# ALLOWED_ORIGINS adds deployed frontend origin(s) (e.g. the Vercel URL) on
# top of the two local dev origins, as a comma-separated list — set it in
# the hosting provider's env vars rather than hardcoding a production domain.
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

app.include_router(matches.router)
app.include_router(calibration.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check: confirms the server is up and responding."""
    return {"status": "ok"}
