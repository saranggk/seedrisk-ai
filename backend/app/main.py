"""
SeedRisk AI backend entrypoint.

Run with: uvicorn app.main:app --reload  (from the backend/ directory)
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Reads backend/.env (if present) into the environment, e.g. ANTHROPIC_API_KEY.
# Safe to call even with no .env file — it's a no-op in that case, so the app
# still runs fine using mock analyst mode.
load_dotenv()

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(matches.router)
app.include_router(calibration.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check: confirms the server is up and responding."""
    return {"status": "ok"}
