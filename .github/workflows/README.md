# Workflow Operations

This directory contains GitHub Actions entry points for `web-ingest`. Task implementation belongs in the corresponding root task directory; workflow files should stay thin.

## Current recurring schedule

All cron expressions are stored in UTC. Human-facing times below use Asia/Singapore (UTC+8).

| Workflow | Local schedule | Timeout | Purpose |
| --- | --- | ---: | --- |
| `ai-daily.yml` | 08:05 daily | 65 min | Wait for and mirror the AIHOT daily snapshot |
| `github-trending.yml` | 09:27 / 10:27 / 11:27 daily | 15 min | Three retry opportunities; first valid snapshot wins |

The schedule is intentionally staggered. `ai-daily` can legitimately spend close to an hour waiting for its upstream publication, so GitHub Trending starts only after its worst-case timeout window plus repository buffer.

## Load-balancing policy

`tools/check-repository-integrity.py` is the source of truth for static schedule validation.

For every recurring workflow:

- declare `timeout-minutes`;
- provide `workflow_dispatch` for manual recovery;
- provide top-level `concurrency` so repeated runs of the same task do not overlap;
- keep its scheduled start outside every other recurring workflow's declared timeout window plus the repository buffer;
- keep cron minutes deliberately non-round when practical, reducing contention with common `:00` schedules on GitHub-hosted runners;
- document the schedule in the task README when behavior changes.

The current cross-workflow planning buffer is **15 minutes** after the declared timeout. This is a planning guard, not a claim that Actions always consume their full timeout.

## CI and maintenance Actions

`repository-integrity.yml` is event-driven only. It runs when repository rules, workflow definitions, or maintenance tools change. Normal daily data commits do not trigger it.

Short event-driven validation may run at the same time as a collection task; it is intentionally lightweight. The load-balancing rule is aimed at recurring ingestion jobs, which are the persistent workload we control.

## Temporary workflows

Backfills, migrations, repairs, probes, and diagnostics are one-shot operations. They must not receive a recurring `schedule:` trigger. Remove temporary workflow files after the operation is validated.

When a large historical repair is needed, prefer batching commits by natural archive boundaries (for example, year) and keep source conversion logic inside the task directory.
