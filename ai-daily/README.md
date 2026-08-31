# AI Daily

Collect the daily report published by **AIHOT**.

## Source

- Site: `https://aihot.virxact.com/`
- REST API v1: `GET https://aihot.virxact.com/api/v1/dailies/latest`
- Daily webpage: use the exact `report.links.aihot` returned by the v1 response.
- AIHOT normally publishes the daily report at 08:00 Beijing time.

This task only collects the AIHOT daily report and its webpage. Downstream Gmail delivery is intentionally outside this repository.

## API migration

This task uses **REST API v1 only**. Do not add new calls to `/api/public/*`.

AIHOT states that `/api/public/*` will stop serving on **2026-12-31**. The old daily endpoints `/api/public/daily` and `/api/public/daily/{date}` are replaced by `/api/v1/dailies/latest` and `/api/v1/dailies/{date}`. The v1 response has a stable outer object and the report body is under `report`.

Do not convert the v1 payload back into the old field shape.

## Schedule

Workflow: `.github/workflows/ai-daily.yml`

The GitHub Action starts every day at **08:05 Beijing time** (`00:05 UTC`).

For a scheduled run, the collector verifies that the returned `report.date` is today's Beijing date. If today's report is not available yet, it retries every 5 minutes, up to 12 attempts. The intended collection window is **08:05–09:00 Beijing time**, with the last attempt at about 09:00.

The workflow can also be run manually with a `YYYY-MM-DD` date to backfill one report.

## Output

A complete daily snapshot contains both files:

```text
ai-daily/data/YYYY/MM/DD/
├── aihot-daily.html
└── aihot-daily.json
```

- `aihot-daily.html` is the **byte-for-byte HTTP response body of the AIHOT daily webpage**. This is the preferred source when a downstream Agent needs to reproduce the page visually.
- `aihot-daily.json` is the **byte-for-byte REST API v1 response body**. This is the preferred structured source for validation and reliable content extraction.

Neither file may be reformatted, normalized, reserialized, have a newline appended, have escaping changed, or otherwise be modified by the collector.

The collector may parse in-memory copies only for validation and for discovering the canonical daily webpage URL.

The raw website HTML is not itself guaranteed to be Gmail-safe: mail clients may strip scripts or unsupported CSS. Any email-compatible transformation belongs downstream; this repository must preserve the original webpage response so the downstream Agent has the best possible source material.

Existing snapshots are not silently overwritten. A rerun with byte-identical content is a no-op; different bytes for an existing file fail so an Agent can inspect the change explicitly.

## Maintenance

When changing or repairing this task:

1. Read this file first.
2. Read `.github/workflows/ai-daily.yml` and `ai-daily/fetch_aihot_daily.py` before editing.
3. Preserve both raw outputs: webpage HTML and REST API v1 JSON.
4. Preserve byte-for-byte mirroring unless the repository owner explicitly changes it.
5. Keep the API contract, schedule, retry behavior, output paths, and backfill behavior documented here when they change.
6. Do not move Gmail sending, summarization, or downstream archive logic into this repository.

## Files

- `ai-daily/fetch_aihot_daily.py` — fetch, validate, retry, and save both original response bodies.
- `.github/workflows/ai-daily.yml` — scheduled/manual GitHub Action.
- `ai-daily/data/` — immutable daily snapshots.
