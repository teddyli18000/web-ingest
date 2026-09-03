# Workflow Operations

This directory contains GitHub Actions entry points for `web-ingest`. Task implementation belongs in the corresponding root task directory; workflow files should stay thin.

## Current recurring schedule

All cron expressions are stored in UTC. Human-facing times below use Asia/Singapore (UTC+8).

| Workflow | Local schedule | Timeout | Purpose |
| --- | --- | ---: | --- |
| `ai-daily-warm.yml` | runner acquisition 04:37 / 05:07 | 230 min | Acquire an AI Daily runner hours before publication and keep it alive across 08:00 |
| `ai-daily.yml` | recovery 09:13 / 10:13 / 11:13 / 11:37 | 3 min | Short recovery opportunities before downstream retries, plus manual backfill |
| `github-trending.yml` | 09:31 / 10:43 / 11:55 daily | 15 min | Three retry opportunities; first valid snapshot wins |
| `google-trending.yml` | 12:37 / 13:49 daily | 15 min | Capture SG + US + GB + HK Trending Now; second slot is retry/no-op |
| `temp-work-cleanup.yml` | 23:17 Sunday | 3 min | Delete first-level `temp-work/` workspaces untouched by meaningful commits for more than one month |

AI Daily is intentionally different from the other collectors because punctuality around an external publication time matters. Its known downstream consumer checks the mirror at 08:15 and then hourly through 12:15.

Two consecutive days showed that several nearby GitHub `schedule` events can be delayed together. On 2026-09-03 the nominal 07:21 / 07:43 / 07:53 / 08:03 AI Daily warm events did not actually start until roughly 09:07 / 09:25 / 09:30 / 10:49, even though AIHOT had generated the report at 08:00. Near-deadline cron hedging is therefore not treated as a reliable way to meet the 08:15 objective.

The warm workflow asks for a runner at **04:37**, with a **05:07** fallback. Both use the same `ai-daily-aihot` concurrency group with `cancel-in-progress: false`. Once one run is executing it remains alive until the publication boundary. At **07:59:45** it starts polling the date-specific AIHOT daily endpoint every **5 seconds**, with each HTTP request bounded to **5 seconds**, through **08:14**. The 230-minute timeout is intentional: acquiring a runner hours early provides enough dispatch-delay budget to absorb scheduler lag comparable to the incidents already observed.

The publication watcher is failure-visible. If the whole warm window ends without a complete validated API + HTML snapshot, the job fails instead of reporting a green no-op. Live 404 responses are treated as pre-publication state and retried; 429 honors `Retry-After`; transient 5xx/network failures use bounded backoff. The task README owns the detailed fetch contract.

The 05:07 nominal start plus the workflow timeout and repository's 15-minute planning buffer reserves AI Daily through **09:12**. Recovery therefore begins at **09:13**, then runs at 10:13 / 11:13 / 11:37 with a short 3-minute timeout. These windows remain clear of GitHub Trending's declared schedule.

This long warm hold is a documented exception to the normal preference against idle Actions. `web-ingest` is public, and retaining a runner already acquired materially improves the reliability of a time-sensitive collector.

## Load-balancing policy

`tools/check-repository-integrity.py` is the source of truth for static schedule validation.

For every recurring workflow:

- declare `timeout-minutes`;
- provide `workflow_dispatch` for manual recovery or operator testing;
- provide top-level concurrency so repeated runs of the same task do not overlap;
- keep its scheduled start outside every other recurring workflow's declared timeout window plus the repository buffer;
- use deliberately different non-round cron minutes where practical rather than copying one minute across bots;
- keep collection workflows schedule/manual only; code-change validation belongs to repository-integrity CI.

Most scheduled workflows are owned by a same-named root task directory. Durable exceptions where multiple workflow entry points belong to one task must be explicitly registered in `tools/check-repository-integrity.py` with the owning README. Repository-wide maintenance uses the same mechanism. Disposable backfill/repair/probe workflows remain forbidden from receiving recurring schedules.

The cross-workflow planning buffer is **15 minutes** after the declared timeout. Multiple retry slots inside one idempotent workflow may overlap one another logically; top-level concurrency serializes actual execution, while each run must check whether its intended output already exists.

Scheduled Actions are not exact clocks. For a task with a hard publication boundary, acquire the runner far enough in advance to absorb observed scheduler delay and keep that runner alive rather than depending on a fresh near-deadline dispatch.

## CI and maintenance Actions

`repository-integrity.yml` is event-driven only. It validates repository rules, recurring schedules, task tests, and Python repository-management tools. Normal daily data commits do not trigger it.

`temp-work-cleanup.yml` is the durable lifecycle manager for `temp-work/`. It is API-only, writes only when stale first-level workspaces actually need deletion, and records its audit trail in the Action Step Summary instead of committing status files.

This is a public repository, so useful Actions execution is not treated as scarce private-runner budget. Reproduction, testing, validation, probes, and intentional warm-runner holding may use Actions time when that materially improves reliability. Public visibility is the hard constraint: workflows must not expose credentials, private data, private repository content, signed URLs, sensitive environment dumps, or secret-derived material.

## Temporary workflows

Backfills, migrations, repairs, probes, diagnostics, and smoke tests are one-shot operations. They must not receive a recurring `schedule:` trigger and must self-remove or be removed after validation.

Large historical repairs should batch commits by natural archive boundaries such as year. Temporary manager scripts belong under `tools/` or, when they are experiment-specific and disposable, inside their `temp-work/<work-name>/` workspace; durable task schema/source rules belong in the task directory.
