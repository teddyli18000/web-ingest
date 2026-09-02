# Workflow Operations

This directory contains GitHub Actions entry points for `web-ingest`. Task implementation belongs in the corresponding root task directory; workflow files should stay thin.

## Current recurring schedule

All cron expressions are stored in UTC. Human-facing times below use Asia/Singapore (UTC+8).

| Workflow | Local schedule | Timeout | Purpose |
| --- | --- | ---: | --- |
| `ai-daily.yml` | scheduler hedges 05:53 / 06:13 / 06:33 / 06:53 / 07:13 / 07:33 / 07:53 / 08:13; recovery 08:29 / 09:03 / 10:11 / 11:27 | 13 min | Hedge correlated GitHub scheduler delay before the downstream 08:15 check, then recover only inside its retry window |
| `github-trending.yml` | 09:31 / 10:43 / 11:55 daily | 15 min | Three retry opportunities; first valid snapshot wins |
| `google-trending.yml` | 12:37 / 13:49 daily | 15 min | Capture SG + US + GB + HK Trending Now; second slot is retry/no-op |
| `temp-work-cleanup.yml` | 23:17 Sunday | 3 min | Delete first-level `temp-work/` workspaces untouched by meaningful commits for more than one month |

AI Daily is intentionally different from the other collectors because punctuality around an external publication time matters. Its known downstream consumer checks the mirror at 08:15 and then hourly through 12:15, so collection effort is concentrated before the first check and only retained while those retries can still consume the result. There are no afternoon/evening AI Daily recovery slots after that useful window.

AI Daily does not assume that schedule delay is independent between nearby cron events. Its primary nominal events are spread from 05:53 through 08:13 at 20-minute spacing. An event that actually starts before 07:49 is only a cheap one-shot probe; if GitHub delays that same event into 07:49-08:15, it automatically becomes a dense 10-second publication watcher. This turns early cron events into scheduler-lag hedges without keeping runners or the AIHOT endpoint busy for hours when GitHub is punctual.

The schedule deliberately uses different non-round minutes. Under the timeout + 15-minute planning-buffer rule, AI Daily's 09:03 slot reserves through 09:31, its 10:11 slot through 10:39, and its 11:27 slot through 11:55. These exact boundaries remain non-overlapping with GitHub Trending at 09:31 / 10:43 / 11:55. GitHub Trending's final 11:55 slot reserves through 12:25; Google Trending therefore starts at 12:37. The weekly temp-work cleanup is far outside the collector window and is validated by the same schedule guard.

## Load-balancing policy

`tools/check-repository-integrity.py` is the source of truth for static schedule validation.

For every recurring workflow:

- declare `timeout-minutes`;
- provide `workflow_dispatch` for manual recovery;
- provide top-level concurrency so repeated runs of the same task do not overlap;
- keep its scheduled start outside every other recurring workflow's declared timeout window plus the repository buffer;
- use deliberately different non-round cron minutes where practical rather than copying one minute across bots;
- keep collection workflows schedule/manual only; code-change validation belongs to repository-integrity CI.

Persistent repository-wide maintenance schedules must be explicitly registered by the integrity checker with their ownership README. Disposable backfill/repair/probe workflows remain forbidden from receiving recurring schedules.

The cross-workflow planning buffer is **15 minutes** after the declared timeout. Multiple retry slots inside one idempotent workflow may overlap one another logically; top-level concurrency serializes actual execution, while each run must check whether its intended output already exists.

Scheduled Actions are not exact clocks. GitHub schedule events may be delayed or dropped under load, and nearby events can be delayed together. A task that needs punctual collection should hedge scheduler lag across a sufficiently wide nominal window, keep early on-time probes cheap, and remain idempotent when delayed opportunities eventually arrive.

## CI and maintenance Actions

`repository-integrity.yml` is event-driven only. It validates repository rules, recurring schedules, task tests, and Python repository-management tools. Normal daily data commits do not trigger it.

`temp-work-cleanup.yml` is the durable lifecycle manager for `temp-work/`. It is API-only, writes only when stale first-level workspaces actually need deletion, and records its audit trail in the Action Step Summary instead of committing status files.

This is a public repository, so useful Actions execution is not treated as scarce private-runner budget. Reproduction, testing, validation, probes, and short-lived experiments may use Actions aggressively when that materially improves reliability or evidence. Public visibility is the hard constraint: workflows must not expose credentials, private data, private repository content, signed URLs, sensitive environment dumps, or secret-derived artifacts/logs.

## Temporary workflows

Backfills, migrations, repairs, probes, diagnostics, and smoke tests are one-shot operations. They must not receive a recurring `schedule:` trigger and must self-remove or be removed after validation.

Large historical repairs should batch commits by natural archive boundaries such as year. Temporary manager scripts belong under `tools/` or, when they are experiment-specific and disposable, inside their `temp-work/<work-name>/` workspace; durable task schema/source rules belong in the task directory.
