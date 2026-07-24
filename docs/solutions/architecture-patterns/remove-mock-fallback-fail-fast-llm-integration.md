---
title: Fail-fast beats a silent mock fallback once an LLM key is always required
date: 2026-07-24
category: architecture-patterns
module: "backend/app/services (analyst_generator.py, picks_analyst.py) + backend/app/main.py startup check"
problem_type: architecture_pattern
component: assistant
severity: medium
applies_when:
  - "Deciding whether a service layer wrapping a third-party LLM API call should silently degrade to a canned/templated response or fail loudly when the API is unavailable"
  - "An app has an env-gated integration (e.g. ANTHROPIC_API_KEY) that previously had a 'demo mode' fallback and the team has moved to always requiring the real credential"
  - "Choosing between fail-fast-at-startup (refuse to boot without required config) versus fail-fast-at-call-site (raise a typed exception that the router converts to a 5xx)"
tags: [fail-fast, claude-api, mock-fallback-removal, error-handling, service-layer, startup-validation]
---

# Fail-fast beats a silent mock fallback once an LLM key is always required

## Context

SeedRisk's Claude analyst layer (`POST /matches/{id}/analysis` and `POST /picks/analysis`) originally had a mock fallback: if `ANTHROPIC_API_KEY` was unset, or the Claude call failed for any reason, the service quietly returned a deterministic templated report instead, tagged `"source": "mock"` so the frontend could show a "Demo mode" banner. That made sense early on — it let the app run and be demoed without anyone needing a real API key. This rationale was itself backfilled into `docs/DECISIONS.md` as ADR-3 on 2026-07-17, during a documentation pass — not designed fresh at that time, just recorded as already-shipped behavior (per session history; see "Related" below).

The project always has a real key now, and the fallback had become dead weight: two code paths to maintain in every analyst service, a `source` field threaded through backend models and frontend types solely to distinguish real output from fabricated output, and a frontend banner component that existed only to warn about a state that no longer happens. Worse, as the project moves toward deployment, that same fallback becomes a liability rather than a convenience: a misconfigured `ANTHROPIC_API_KEY` on the hosting platform would silently serve real visitors fabricated "analyst" text with a 200 response, rather than surfacing the misconfiguration in any visible way.

## Guidance

When a fallback path exists only to accommodate a constraint that no longer applies — "should work without X" when X is now always present — don't let it linger. Remove it, and make the missing-X case fail loudly rather than degrade silently. Prefer catching the problem as early as possible: a missing required config value should fail at process startup, not at first request, so a bad deploy never serves a single request before the operator notices.

This is a choice between two failure philosophies:
- **Fail-open**: silently substitute fake/mock/default data so the request "succeeds," hiding the underlying problem from whoever is looking at the response.
- **Fail-loud**: refuse to start (for missing config), or return a clear, distinguishable error status (for a runtime failure), so the problem is visible exactly where it occurred.

Once a fallback's original justification is gone, fail-loud is strictly better: it turns a class of silent-correctness bugs into a loud, immediately-debuggable one.

The concrete shape used here has two halves, matched to *when* the failure is knowable:

**Startup-time check for missing required config** (`backend/app/main.py:20-21`):
```python
if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ANTHROPIC_API_KEY is not set. Copy backend/.env.example to backend/.env and add a key.")
```
This runs before the app object is even constructed, so a misconfigured deploy never comes up healthy.

**Dedicated exception type per service, translated to an HTTP status at the router boundary**, for failures that can only be known at request time (e.g. the Claude API itself erroring). Each service module defines its own exception subclassing `RuntimeError` — `AnalystServiceUnavailable` in `analyst_generator.py:34-35`, `PicksAnalystServiceUnavailable` in `picks_analyst.py:18-19` — and the generator function wraps the Claude call:
```python
try:
    return _claude_report(payload)
except (APIError, RuntimeError) as exc:
    raise AnalystServiceUnavailable("Claude analyst report generation failed.") from exc
```
The router then catches that specific exception and converts it to an HTTP error, rather than letting a generic exception escape or — the thing being removed — catching it and returning fabricated success data:
```python
try:
    return generate_analyst_report(match, prediction)
except AnalystServiceUnavailable as exc:
    raise HTTPException(status_code=502, detail="Claude analyst report is temporarily unavailable.") from exc
```
(`backend/app/routers/matches.py:73-76`, mirrored for picks analysis at lines 98-101 with `PicksAnalystServiceUnavailable` → 502.)

A useful side effect of this shape: once there's no second value `source` could ever hold, the field itself becomes meaningless — it was removed from `AnalystReportResponse` and `PicksAnalysisResponse` in `backend/app/models.py` and their `frontend/lib/types.ts` equivalents, and the two "Demo mode" banner blocks that branched on `source === "mock"` were deleted from `frontend/components/AnalystReportSection.tsx` and `frontend/app/page.tsx`. No new frontend error handling was needed for the 502 case: `AnalystReportSection.tsx` already had a generic `{ status: "error"; error: ApiError }` state with a "Couldn't generate the analyst report" panel and "Try again" button, wired to catch any thrown `ApiError` — so the existing error UI now naturally covers real Claude-call failures too, without SeedRisk needing to special-case them.

## Why This Matters

For a deployed, public-facing app, a silent mock fallback is a correctness bug waiting to happen, not a convenience. If `ANTHROPIC_API_KEY` were unset or wrong on the hosting platform, the old code path would have served every visitor a plausible-looking but entirely fabricated "analyst" report with a 200 response — no error, no banner distinguishing it from a real analysis, and no signal to the operator that anything was wrong. The new behavior makes that scenario impossible to ship silently: the process won't even boot without a key, and a runtime Claude failure surfaces as a 502 the existing error UI already renders visibly. The cost of being loud (a crashed process, a visible error panel) is trivial compared to the cost of being wrong invisibly.

## When to Apply

- When a fallback or mock path was added for local-dev convenience early in a project — e.g. "run without needing an API key yet" — but the constraint it accommodated no longer holds.
- When preparing to deploy: audit the codebase for silent-degradation paths specifically, since a misconfigured production environment variable turns a previously-harmless fallback into a correctness bug that fabricates data for real users.
- Not a universal rule. Mock/fallback modes are still the right design when the app genuinely needs to work without an external dependency — e.g. an open-source project that other people will clone and run without their own API key, or a demo mode that's an intentional, clearly-labeled product feature rather than a silent substitution. This guidance applies once "should work without X" is no longer actually true for the project in question.

## Examples

Before (representative of the removed shape — not the literal prior code, since it's been deleted):
```python
def generate_analyst_report(match, prediction):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return _mock_report(match, prediction)  # source="mock"
    try:
        return _claude_report(match, prediction)
    except Exception:
        return _mock_report(match, prediction)  # source="mock"
```

After (actual current code, `backend/app/services/analyst_generator.py:97-103`):
```python
def generate_analyst_report(match: Match, prediction: PredictionResponse) -> AnalystReportResponse:
    payload = _build_payload(match, prediction)
    try:
        return _claude_report(payload)
    except (APIError, RuntimeError) as exc:
        raise AnalystServiceUnavailable("Claude analyst report generation failed.") from exc
```

Router boundary translating the service exception to a status code (`backend/app/routers/matches.py:73-76`):
```python
try:
    return generate_analyst_report(match, prediction)
except AnalystServiceUnavailable as exc:
    raise HTTPException(status_code=502, detail="Claude analyst report is temporarily unavailable.") from exc
```

Startup guard, added alongside the router changes (`backend/app/main.py:20-21`):
```python
if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ANTHROPIC_API_KEY is not set. Copy backend/.env.example to backend/.env and add a key.")
```

Same pattern repeated independently for picks analysis: `PicksAnalystServiceUnavailable` (`backend/app/services/picks_analyst.py:18-19`, raised at lines 130-133) caught in `backend/app/routers/matches.py:98-101` and turned into a 502 with detail `"Claude picks analysis is temporarily unavailable."`

## Related

- `docs/DECISIONS.md` — ADR-3 ("Deterministic mock mode when no API key is set") documents the *removed* behavior as current and is now stale as of this change; flagged for a `ce-compound-refresh` pass rather than edited here.
- `docs/METHODOLOGY.md` — its "Mock mode" section (pointing to ADR-3) is stale for the same reason.
- No related `docs/solutions/` entries or GitHub issues found — this is the first `ce-compound` documentation run in this repository.
