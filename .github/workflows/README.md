# Workflow Operations

This directory contains GitHub Actions entry points for `web-ingest`. Task implementation belongs in the corresponding root task directory; workflow files should stay thin.

## Current recurring schedule

All cron expressions are stored in UTC. Human-facing times below use Asia/Singapore (UTC+8).

| Workflow | Local schedule | Timeout | Purpose |
| --- | --- | ---: | --- |
| `ai-daily-warm.yml` | runner acquisition 07:21 / 07:43 / 07:53 / 08:03 | 52 min | Acquire a runner before AIHOT publication, keep an acquired runner alive, and provide later acquisition fallbacks if earlier scheduled runs never start |
| `ai-daily.yml` | recovery 09:11 / 10:11 / 11:13 / 11:37 | 3 min | Short recovery opportunities immediately before useful downstream retries, plus manual backfill |
| `github-trending.yml` | 09:31 / 10:43 / 11:55 daily | 15 min | Three retry opportunities; first valid snapshot wins |
| `google-trending.yml` | 12:37 / 13:49 daily | 15 min | Capture SG + US + GB + HK Trending Now; second slot is retry/no-op |
| `temp-work-cleanup.yml` | 23:17 Sunday | 3 min | Delete first-level `temp-work/` workspaces untouched by meaningful commits for more than one month |

AI Daily is intentionally different from the other collectors because punctuality around an external publication time matters. Its known downstream consumer checks the mirror at 08:15 and then hourly through 12:15.

The warm workflow therefore uses a **runner-acquisition ladder**. It asks GitHub for a runner at 07:21, then creates additional opportunities at 07:43, 07:53, and 08:03. All runs use the same `ai-daily-aihot` concurrency group with `cancel-in-progress: false`. Once one run is actually executing, it remains the active run; later opportunities are only fallbacks for cases where an earlier scheduled event never becomes an executing runner. GitHub's default single-pending concurrency behavior means a newer pending opportunity can replace an older pending one while the current active run is preserved.

An acquired warm runner waits until 07:57, polls AIHOT every 10 seconds through 08:10, and performs a short immediate recovery attempt when it starts after that warm window. The 52-minute timeout lets a punctual 07:21 run stay alive across the intended publication window. The latest nominal 08:03 slot plus the repository's 15-minute planning buffer reserves this workflow through 09:10.

Recovery then starts at 09:11 with a short 3-minute timeout. Its later 10:11, 11:13, and 11:37 slots are arranged around the downstream retry times while remaining clear of GitHub Trending's declared windows. Warm and recovery share the same concurrency group, so delayed AI Daily runs do not write the task concurrently.

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

Scheduled Actions are not exact clocks. GitHub schedule events may be delayed or dropped under load. For a task with a hard publication boundary, repeated acquisition opportunities plus holding an already-acquired runner are preferred over releasing a runner and depending on a fresh near-deadline dispatch.

## CI and maintenance Actions

`repository-integrity.yml` is event-driven only. It validates repository rules, recurring schedules, task tests, and Python repository-management tools. Normal daily data commits do not trigger it.

`temp-work-cleanup.yml` is the durable lifecycle manager for `temp-work/`. It is API-only, writes only when stale first-level workspaces actually need deletion, and records its audit trail in the Action Step Summary instead of committing status files.

This is a public repository, so useful Actions execution is not treated as scarce private-runner budget. Reproduction, testing, validation, probes, and intentional warm-runner holding may use Actions time when that materially improves reliability. Public visibility is the hard constraint: workflows must not expose credentials, private data, private repository content, signed URLs, sensitive environment dumps, or secret-derived artifacts/logs.

## Temporary workflows

Backfills, migrations, repairs, probes, diagnostics, and smoke tests are one-shot operations. They must not receive a recurring `schedule:` trigger and must self-remove or be removed after validation.

Large historical repairs should batch commits by natural archive boundaries such as year. Temporary manager scripts belong under `tools/` or, when they are experiment-specific and disposable, inside their `temp-work/<work-name>/` workspace; durable task schema/source rules belong in the task directory.
