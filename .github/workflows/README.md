# Workflow Operations

This directory contains GitHub Actions entry points for `web-ingest`. Task implementation belongs in the corresponding root task directory; workflow files should stay thin.

## Current recurring schedule

All cron expressions are stored in UTC. Human-facing times below use Asia/Singapore (UTC+8).

| Workflow | Local schedule | Timeout | Purpose |
| --- | --- | ---: | --- |
| `ai-daily.yml` | 07:51 / 07:57 / 08:03 / 08:09 / 08:13; recovery 08:29 / 09:03 / 10:11 / 11:27 | 13 min | Race AIHOT publication before the downstream 08:15 check, then recover only inside its retry window |
| `github-trending.yml` | 09:31 / 10:43 / 11:55 daily | 15 min | Three retry opportunities; first valid snapshot wins |
| `google-trending.yml` | 12:37 / 13:49 daily | 15 min | Capture SG + US + GB + HK Trending Now; second slot is retry/no-op |

AI Daily is intentionally different from the other collectors because punctuality around an external publication time matters. Its known downstream consumer checks the mirror at 08:15 and then hourly through 12:15, so collection effort is concentrated before the first check and only retained while those retries can still consume the result. There are no afternoon/evening AI Daily recovery slots after that useful window.

The primary AI Daily events begin at 07:51 and repeat through 08:13. A run that begins before 08:15 polls every 10 seconds; once a complete same-day snapshot reaches `main`, every later run becomes a fast no-op. Recovery events at 08:29 / 09:03 / 10:11 / 11:27 cover the remaining downstream retry window.

The schedule deliberately uses different non-round minutes. Under the timeout + 15-minute planning-buffer rule, AI Daily's 09:03 slot reserves through 09:31, its 10:11 slot through 10:39, and its 11:27 slot through 11:55. These exact boundaries remain non-overlapping with GitHub Trending at 09:31 / 10:43 / 11:55. GitHub Trending's final 11:55 slot reserves through 12:25; Google Trending therefore starts at 12:37.

## Load-balancing policy

`tools/check-repository-integrity.py` is the source of truth for static schedule validation.

For every recurring workflow:

- declare `timeout-minutes`;
- provide `workflow_dispatch` for manual recovery;
- provide top-level `concurrency` so repeated runs of the same task do not overlap;
- keep its scheduled start outside every other recurring workflow's declared timeout window plus the repository buffer;
- use deliberately different non-round cron minutes where practical rather than copying one minute across bots;
- keep collection workflows schedule/manual only; code-change validation belongs to repository-integrity CI.

The cross-workflow planning buffer is **15 minutes** after the declared timeout. Multiple retry slots inside one idempotent workflow may overlap one another logically; top-level concurrency serializes actual execution, while each run must check whether its intended output already exists.

Scheduled Actions are not treated as exact clocks. GitHub documents that schedule events may be delayed or dropped under load. A task that needs punctual collection should use independent opportunities and idempotent recovery rather than one long sleeping runner.

## CI and maintenance Actions

`repository-integrity.yml` is event-driven only. It validates repository rules, recurring schedules, task tests, and Python repository-management tools. Normal daily data commits do not trigger it.

## Temporary workflows

Backfills, migrations, repairs, probes, diagnostics, and smoke tests are one-shot operations. They must not receive a recurring `schedule:` trigger and must self-remove or be removed after validation.

Large historical repairs should batch commits by natural archive boundaries such as year. Temporary manager scripts belong under `tools/`; durable task schema/source rules belong in the task directory.
