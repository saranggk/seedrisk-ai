# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Claude analyst layer

### Claude analyst layer
The part of SeedRisk that turns an already-computed prediction into plain-English explanation. It never computes or changes a prediction's numbers (probabilities, risk label, factor impacts) — it only narrates data it's handed, constrained by a structured-output schema that has no field where it could insert a number of its own.

### Analyst report
A single match's Claude-written explanation, structured as seven fixed fields (match summary, why the favourite is favoured, why an upset could happen, key stat to watch, upset recipe, final take, confidence note). Generated on demand per match, grounded strictly in that match's prediction data.

### Picks analysis
The Claude analyst layer's portfolio-level counterpart to an Analyst report: grades a user's whole slate of Pick Mode choices against the model's predictions and writes a summary of the slate as a whole, rather than explaining a single match.
