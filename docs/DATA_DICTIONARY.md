# Data Dictionary — `data/sample_matches.json`

This file is **synthetic sample data** styled after Wimbledon-style grass court tennis. Player names and stats are fictional — they exist to build and test the app, not to represent real players or real outcomes.

## Shape of the file

The file is a JSON array of **matches**. Each match has:

| Field | Type | Meaning |
|---|---|---|
| `match_id` | string | Unique ID for the match (e.g. `"M001"`). Used to look up a specific match later via the API. |
| `round` | string | Tournament round the match is in: `R1`–`R4` (rounds of 128/64/32/16), `QF` (quarterfinal), `SF` (semifinal), `F` (final). Later rounds generally mean tougher, more in-form opponents. |
| `favorite` | object | The player expected to win, based on ranking/seeding. See player fields below. |
| `underdog` | object | The player expected to lose. Same fields as `favorite`. |

Every match has exactly one favorite and one underdog — that pairing is the core unit the rest of the app reasons about.

## Player fields (inside `favorite` and `underdog`)

| Field | Type | Plain-English meaning | Why it matters for upset prediction |
|---|---|---|---|
| `player_name` | string | The player's display name. | Identifies who's playing; shown in the UI. |
| `ranking` | int | Current ATP/WTA-style world ranking (lower = better). | The single biggest signal of "who's the favorite" — but rankings reflect overall form across *all* surfaces, not grass specifically, so they can be misleading at Wimbledon. |
| `seed` | int or `null` | Tournament seed number, or `null` if unseeded. | Seeding affects draw position and is a public signal of how much the tournament itself rates this player; unseeded players beating seeds is the classic definition of an "upset." |
| `grass_win_pct` | float (0–1) | Win percentage on grass courts specifically. | Grass plays very differently from hard/clay (faster, lower bounce, more reliant on serve). A favorite with a mediocre grass record is more vulnerable than their ranking suggests. |
| `recent_win_pct` | float (0–1) | Win percentage over recent matches (current form), regardless of surface. | Captures short-term form/momentum — a slumping favorite is more upset-prone even if their ranking hasn't caught up yet. |
| `wimbledon_win_pct` | float (0–1) | Historical win percentage specifically at Wimbledon. | Some players have a track record of over- or under-performing at this exact event (crowd, scheduling, grass familiarity, etc.). |
| `hold_rate_grass` | float (0–1) | Percentage of own service games won, on grass. | On grass, service holds are everything — a favorite with a shaky hold rate is one bad service game away from trouble. |
| `break_rate_grass` | float (0–1) | Percentage of opponent's service games broken, on grass. | Measures a player's ability to actually create upset opportunities by breaking serve — relevant both for how dangerous the underdog is and how exposed the favorite is. |
| `tiebreak_win_pct` | float (0–1) | Win percentage in tiebreaks. | Grass matches are tiebreak-heavy (few breaks of serve). A player who is mediocre in tiebreaks can lose a match despite playing well overall — a classic upset mechanism. |
| `last_10_record` | string (`"W-L"`) | Win-loss record over the last 10 matches, e.g. `"7-3"`. | A compact, human-readable form snapshot, easy to show directly in the UI alongside the win-pct stats. |
| `h2h_wins` | int | Number of times this player has beaten the *other player in this specific match*. | Head-to-head history can override general form — some players consistently struggle against a specific opponent's style. |
| `h2h_losses` | int | Number of times this player has lost to the *other player in this specific match*. | Same as above — together `h2h_wins`/`h2h_losses` describe the rivalry record from this match. |

**Note on h2h fields:** `h2h_wins`/`h2h_losses` are always relative to the specific opponent faced *in that match* — they are not a player's career head-to-head average. So `favorite.h2h_wins` and `underdog.h2h_losses` describe the same rivalry from each side's perspective and should mirror each other.

## What's intentionally *not* here yet

- No upset probability, risk label, or model output — that's Phase 4.
- No database — this is flat JSON for now; Phase 2 loads it into SQLite.
- No real-world player data — everything is fictional sample data.
