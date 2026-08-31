# AI Daily

Collect the daily report published by **AIHOT**.

## Source

- Site: `https://aihot.virxact.com/`
- API: `GET https://aihot.virxact.com/api/v1/dailies/latest`
- AIHOT publishes its daily report at 08:00 Beijing time.

Only the AIHOT daily report is collected by this task.

## Schedule

Workflow: `.github/workflows/ai-daily.yml`

The GitHub Action starts every day at **08:17 Beijing time** (`00:17 UTC`).

For a scheduled run, the collector verifies that the returned `report.date` is today's Beijing date. If today's report is not available yet, it retries every 5 minutes, up to 10 attempts. The normal collection window is therefore roughly 08:17–09:02.

The workflow can also be run manually with a `YYYY-MM-DD` date to backfill one report.

## Output

Each report is stored as the complete API v1 JSON response:

```text
ai-daily/data/YYYY/MM/DD/aihot-daily.json
```

Existing snapshots are not silently overwritten. A rerun with identical content is a no-op; different content for an existing date fails so an Agent can inspect the change explicitly.

## Maintenance

When changing or repairing this task:

1. Read this file first.
2. Read `.github/workflows/ai-daily.yml` and `ai-daily/fetch_aihot_daily.py` before editing.
3. Keep the source contract, schedule, retry behavior, output path, and backfill behavior documented here when they change.
4. Do not move downstream summarization, archiving, or email delivery into this repository.

## Files

- `ai-daily/fetch_aihot_daily.py` — fetch, validate, retry, and save one report.
- `.github/workflows/ai-daily.yml` — scheduled/manual GitHub Action.
- `ai-daily/data/` — immutable daily snapshots.
