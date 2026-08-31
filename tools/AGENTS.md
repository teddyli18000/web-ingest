# AGENTS.md — tools

`tools/` is the repository manager workspace for `web-ingest`.

It may contain more than one tool. Use it for repository-wide guards, schedule inspection, audits, migration helpers, maintenance notes, and other small utilities that make the repository easier to operate safely.

## Boundaries

- Task-specific collection/parsing logic belongs under that task's root directory, not here.
- A tool belongs here when it manages or validates multiple tasks or the repository itself.
- Keep tools inspectable and dependency-light; prefer the Python standard library for repository guards.
- Do not make tools fetch private data or require secrets unless the repository owner explicitly changes that policy.
- A maintenance tool must fail clearly: report the exact file/rule/conflict rather than silently fixing unrelated state.

## Scheduling

`check-repository-integrity.py` is the canonical static guard for scheduled Actions.

When adding or changing a recurring workflow:

1. Give it an explicit `timeout-minutes`.
2. Give it a top-level `concurrency` group and a manual `workflow_dispatch` path.
3. Stagger it from other recurring workflows using the repository guard's timeout-window + buffer policy.
4. Run `python tools/check-repository-integrity.py --show` and inspect the resulting local schedule.
5. Do not weaken the guard merely to fit a new cron. Move the cron unless there is a documented reason to change repository policy.

## Notes and maintenance state

Short repository-maintenance notes may live here when they are useful to future Agents. Prefer concise Markdown that records current decisions, known issues, and superseded assumptions. Remove obsolete transient notes once their decisions have been incorporated into durable README/AGENTS rules.

## Temporary work

One-shot migration/backfill/repair/probe workflows must not become recurring jobs. If a temporary Action is required, make its purpose obvious and remove it after successful validation.
