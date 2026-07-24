# SeedRisk AI — Methodology

How the upset-risk model works, what the Claude analyst layer does, and what the current limitations are.

---

## Why a rule-based model?

See [`docs/DECISIONS.md` — ADR-1](DECISIONS.md#adr-1-rule-based-scoring-not-a-trained-ml-model) for why the MVP uses rule-based scoring instead of a trained model, and for the planned path to a trained model behind the same output interface.

---

## Features and their roles

The model evaluates each match on the following features:

| Feature | What it captures |
|---|---|
| Ranking gap | Large gaps protect the favourite; small gaps increase upset risk |
| Grass-court win % | Historical grass performance for both players |
| Recent form (win %) | Win rate over recent matches — a proxy for current confidence |
| Wimbledon-specific win % | Tournament-specific history on this surface |
| Grass serve hold rate | Holding serve on grass is critical; a weak holder is vulnerable |
| Grass return/break rate | Breaking the favourite's serve is the underdog's primary path |
| Tiebreak win % | Tiebreaks are decisive on grass; strong tiebreak form reduces upset risk |
| Last 10 record | Very recent results (encoded as win/loss percentage) |
| Head-to-head record | Direct history against this specific opponent |

---

## How feature contributions work

After the model runs, each feature produces:

- `impact` — a signed value indicating how much this feature moved the upset probability
- `direction` — one of `increases_upset_risk`, `decreases_upset_risk`, or `neutral`
- `reason` — a human-readable explanation of the direction and magnitude

A positive impact + `increases_upset_risk` means this stat helps the underdog. A negative impact + `decreases_upset_risk` means this stat protects the favourite. Neutral means this feature had minimal influence on the result.

The `top_factors` field returns the 3 features with the **largest absolute impact** — not necessarily the "top upset reasons." A factor can lead that list because it strongly protects the favourite (e.g. a big ranking gap), not just because it threatens them.

---

## Risk labels

The final upset probability maps to a label:

| Label | Trigger | Meaning |
|---|---|---|
| Low | upset probability < 20% | Favourite is heavily favoured; upset is unlikely |
| Medium | 20% ≤ upset probability < 35% | Meaningful upset risk, but the favourite is still expected to win |
| High | upset probability ≥ 35% | Significant upset risk — the match could go either way |
| Trap Match | upset probability ≥ 30% AND ranking gap ≥ 40 | Narrative override — see below |

See [`docs/DECISIONS.md` — ADR-4](DECISIONS.md#adr-4-trap-match-as-its-own-label-not-folded-into-mediumhigh) for why Trap Match is its own narrative-override label rather than a higher probability bucket.

---

## Calibration: checking the model against real outcomes

Everything above describes what the model predicts. Separately, `backend/scripts/backtest_calibration/` checks *how good those predictions actually are* against real history: it scores ~723 real ATP/WTA Wimbledon matches (2021–2025, from `data/wimbledon_backtest_matches.json` — see `docs/DATA_DICTIONARY.md`) through the live `predict_upset()` function and computes:

- **Brier score** — the standard proper scoring rule for probabilistic predictions (lower is better; 0 is a perfect prediction, 0.25 is what a coin-flip-confidence model scores against a 50/50 outcome).
- **Reliability bins** — matches grouped into 0.05-wide predicted-probability buckets (e.g. "predicted 90–95% favourite"), each reporting how often the favourite *actually* won in that bucket. A well-calibrated model's observed rate should track its predicted rate closely within each bin.

The committed result is `data/calibration_report.json`. `GET /calibration` exposes its `reliability_bins` (only that field — not the Brier score or the tour/risk-label breakdowns) to the live API, and the frontend uses it to bucket each prediction into "Likely" (risk label Low) / "Toss-up" (Medium) / "Underdog Alert" (High or Trap Match) and, where a bin has at least 20 historical matches, states the model's real observed accuracy at that confidence level. Thinner bins show the bucket label alone — a bin with 1 or 3 historical matches isn't a reliable estimate of anything, and quoting one as if it were would undercut the entire point of showing real data instead of a bare percentage.

This is diagnostic/informational only: it does not feed back into `predict_upset()`'s weights or thresholds, and it does not run against the synthetic `data/sample_matches.json` the live dashboard actually displays — it's checked against the separate, real dataset instead. Regenerate it with `python -m scripts.backtest_calibration.main` whenever the real dataset changes.

---

## What Claude does and does not do

The Claude analyst layer (`POST /matches/{id}/analysis`) receives:

- Match metadata (round, both players' names)
- Both players' full stat objects — exactly the same data shown in the player comparison table
- The already-computed prediction: `favorite_win_probability`, `upset_probability`, `risk_label`
- The `top_factors` list
- All `feature_contributions` with impact and direction

Claude then writes a structured 7-field report grounded strictly in that data.

**What Claude cannot do:**
- Change any number from the prediction — the response schema has no field for it
- Invent facts not present in the supplied data (no outside knowledge about injuries, rankings, or head-to-heads beyond what is explicitly given)
- Give betting advice (the system prompt explicitly prohibits this)

**What Claude does do:**
- Writes clear, specific prose connecting the feature contributions into a coherent narrative
- Identifies what would need to happen for an upset, based on the model's own factors
- Notes limitations via `confidence_note` when the supplied data is insufficient to support a claim
- Clearly frames the report as an explanation of a statistical model, not a guarantee of the outcome

---

## Mock mode

If `ANTHROPIC_API_KEY` is not set, or the Claude call fails for any reason (rate limit, network error, bad key), the endpoint returns a deterministic mock report built directly from the same rule-based output. The `source` field in the response is `"mock"` (vs `"claude"` for a live call) so the frontend shows a "Demo mode" notice.

See [`docs/DECISIONS.md` — ADR-3](DECISIONS.md#adr-3-deterministic-mock-mode-when-no-api-key-is-set) for why mock mode exists.

---

## Sample data limitations

The current dataset (`data/sample_matches.json`) consists of 16 manually crafted matches designed to cover all four risk label buckets (Low, Medium, High, Trap Match). It is **not real ATP/WTA data**. The model itself *has* been checked against real historical outcomes (see "Calibration" above) — but against a separate real dataset, not this one; the live dashboard's own 16 matches remain synthetic.

Specific limitations:
- No real player stats — all values are plausible but synthetic
- Small dataset — no statistical patterns can be drawn from 16 matches
- No temporal variation — all matches are treated as equally recent
- No real head-to-head history

---

## Future model and data improvements

- **Real data ingestion for the live app** — the calibration check above already runs against real historical data; the *live* dashboard still runs on synthetic `data/sample_matches.json`. Connecting a real ATP/WTA data source to the live app (not just the offline calibration check) remains future work.
- **Model upgrade** — replace rule-based scoring with logistic regression or XGBoost trained on the real historical data, while keeping the same output interface (`feature_contributions`, `risk_label`, etc.)
- **Feature expansion** — add surface-specific head-to-head records, fatigue proxy (recent match count), serve speed data, and seeding-specific information
- **Tighter calibration bins** — right now, thin reliability bins (see above) just get a plain label with no rate quoted; a larger real dataset would let more of the probability range carry a trustworthy observed-rate annotation
