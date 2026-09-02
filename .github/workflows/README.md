# Workflow Operations

This directory contains GitHub Actions entry points for `web-ingest`. Task implementation belongs in the corresponding root task directory; workflow files should stay thin.

## Current recurring schedule

All cron expressions are stored in UTC. Human-facing times below use Asia/Singapore (UTC+8).

| Workflow | Local schedule | Timeout | Purpose |
| --- | --- | ---: | --- |
| `ai-daily-warm.yml` | 07:21 daily | 65 min | Acquire a runner before AIHOT's expected 08:00 publication, hold it until 07:58, then poll across the publication boundary |
| `ai-daily.yml` | recovery 08:43 / 09:03 / 10:11 / 11:27 | 13 min | Short recovery opportunities plus manual backfill |
| `github-trending.yml` | 09:31 / 10:43 / 11:55 daily | 15 min | Three retry opportunities; first valid snapshot wins |
| `google-trending.yml` | 12:37 / 13:49 daily | 15 min | Capture SG + US + GB + HK Trending Now; second slot is retry/no-op |
| `temp-work-cleanup.yml` | 23:17 Sunday | 3 min | Delete first-level `temp-work/` workspaces untouched by meaningful commits for more than one month |

AI Daily is intentionally different from the other collectors because punctuality around an external publication time matters. Its known downstream consumer checks the mirror at 08:15 and then hourly through 12:15.

The primary AI Daily workflow therefore **acquires and holds** a runner instead of relying on a fresh scheduled event near 08:00. A nominal 07:21 run checks whether today's snapshot already exists, then stays alive until 07:58 and polls AIHOT every 10 seconds until 08:16. If the 07:21 schedule itself is delayed past the publication window, the same run skips the hold and performs bounded recovery immediately.

The warm workflow's 65-minute timeout plus the repository's 15-minute planning buffer reserves through **08:41**. The first separate recovery slot is therefore **08:43**. Recovery keeps the original short 13-minute timeout; its 09:03 slot reserves through 09:31, its 10:11 slot through 10:39, and its 11:27 slot through 11:55. These boundaries remain non-overlapping with GitHub Trending at 09:31 / 10:43 / 11:55. GitHub Trending's final 11:55 slot reserves through 12:25; Google Trending starts at 12:37.

The warm and recovery workflows share the same `ai-daily-aihot` concurrency group, so delayed runs cannot write AI Daily concurrently.

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

Scheduled Actions are not exact clocks. GitHub schedule events may be delayed or dropped under load. For tasks with a hard publication boundary, acquiring a runner moderately early and deliberately holding it can be preferable to betting on several new dispatches close to the deadline.

## CI and maintenance Actions

`repository-integrity.yml` is event-driven only. It validates repository rules, recurring schedules, task tests, and Python repository-management tools. Normal daily data commits do not trigger it.

`temp-work-cleanup.yml` is the durable lifecycle manager for `temp-work/`. It is API-only, writes only when stale first-level workspaces actually need deletion, and records its audit trail in the Action Step Summary instead of committing status files.

This is a public repository, so useful Actions execution is not treated as scarce private-runner budget. Reproduction, testing, validation, probes, and intentional warm-runner holding may use Actions time when that materially improves reliability. Public visibility is the hard constraint: workflows must not expose credentials, private data, private repository content, signed URLs, sensitive environment dumps, or secret-derived artifacts/logs.

## Temporary workflows

Backfills, migrations, repairs, probes, diagnostics, and smoke tests are one-shot operations. They must not receive a recurring `schedule:` trigger and must self-remove or be removed after validation.

Large historical repairs should batch commits by natural archive boundaries such as year. Temporary manager scripts belong under `tools/` or, when they are experiment-specific and disposable, inside their `temp-work/<work-name>/` workspace; durable task schema/source rules belong in the task directory.
