# AI Daily

Collect the daily report published by **AIHOT**.

## Source

- Site: `https://aihot.virxact.com/`
- API: `GET https://aihot.virxact.com/api/v1/dailies/latest`
- AIHOT publishes its daily report at 08:00 Beijing time.

Only the AIHOT daily report is collected by this task.

## Schedule

Workflow: `.github/workflows/ai-daily.yml`

The GitHub Action starts every day at **08:05 Beijing time** (`00:05 UTC`).

For a scheduled run, the collector verifies that the returned `report.date` is today's Beijing date. If today's report is not available yet, it retries every 5 minutes, up to 12 attempts. The intended collection window is therefore **08:05–09:00 Beijing time**, with the last attempt at about 09:00.

The workflow can also be run manually with a `YYYY-MM-DD` date to backfill one report.

## Output

Each report is stored at:

```text
ai-daily/data/YYYY/MM/DD/aihot-daily.json
```

The file is a **byte-for-byte mirror of the HTTP response body returned by AIHOT**. The collector may parse a separate in-memory copy only for validation; it must not reformat, normalize, reserialize, append a newline, change escaping, reorder fields, or otherwise modify the bytes that are written.

Existing snapshots are not silently overwritten. A rerun with byte-identical content is a no-op; different bytes for an existing date fail so an Agent can inspect the change explicitly.

## Maintenance

When changing or repairing this task:

1. Read this file first.
2. Read `.github/workflows/ai-daily.yml` and `ai-daily/fetch_aihot_daily.py` before editing.
3. Preserve the byte-for-byte mirroring requirement unless the repository owner explicitly changes it.
4. Keep the source contract, schedule, retry behavior, output path, and backfill behavior documented here when they change.
5. Do not move downstream summarization, archiving, or email delivery into this repository.

## Files

- `ai-daily/fetch_aihot_daily.py` — fetch, validate, retry, and save one report without modifying response bytes.
- `.github/workflows/ai-daily.yml` — scheduled/manual GitHub Action.
- `ai-daily/data/` — immutable daily snapshots.
