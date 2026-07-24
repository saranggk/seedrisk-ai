# SeedRisk AI — working preferences

Solo project — no team, no issue tracker, no PR reviewers. It's a portfolio/passion project, not interview prep, and it doubles as a learning vehicle for full-stack + AI work, so explain the "why" behind implementation choices rather than just implementing silently.

## Git

Always commit directly to `main`. Never create feature branches or open PRs — there's no one to review them.

## Skills

Default to the lightweight subset of installed skill plugins (compound-engineering, mattpocock) — most of what they offer is built for teams (ticket queues, multi-agent PR review, hand-off docs), which doesn't apply here:

- Use: `ce-brainstorm`, `ce-plan`, `ce-work`, `ce-debug`, `/tdd`, plain `code-review` (low/medium effort), `ce-commit`, `ce-compound`.
- Skip unless explicitly requested: `lfg`, `ce-babysit-pr`, `ce-code-review`'s multi-agent parallel mode, and any ticket-tracking workflow.

See the global feature-workflow order (`ce-ideate` → `ce-brainstorm` → `ce-plan` → `ce-work` → commit/push) in `~/.claude/CLAUDE.md`.

`ce-compound` writes durable learnings to `docs/solutions/<category>/` (YAML frontmatter: module, tags, problem_type) and shared domain vocabulary to `CONCEPTS.md` — both worth checking when orienting to an area or before re-solving something already documented.
