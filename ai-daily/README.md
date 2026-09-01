# AI Daily

Collect the daily report published by **AIHOT**.

## Source

- Site: `https://aihot.virxact.com/`
- REST API v1: `GET https://aihot.virxact.com/api/v1/dailies/latest`
- Daily webpage: use the exact `report.links.aihot` returned by the v1 response.
- AIHOT normally publishes the daily report at about 08:00 Beijing time.

This task only collects the AIHOT daily report and its webpage. Downstream Gmail delivery is intentionally outside this repository.

## API migration

This task uses **REST API v1 only**. Do not add new calls to `/api/public/*`.

AIHOT states that `/api/public/*` will stop serving on **2026-12-31**. The old daily endpoints `/api/public/daily` and `/api/public/daily/{date}` are replaced by `/api/v1/dailies/latest` and `/api/v1/dailies/{date}`. The v1 response has a stable outer object and the report body is under `report`.

Do not convert the v1 payload back into the old field shape.

## Schedule and reliability

Workflow: `.github/workflows/ai-daily.yml`

This collector is designed to run without an Agent watching it. GitHub documents that scheduled workflow events are best-effort: under high Actions load they may be delayed and, in severe cases, queued runs may be dropped. The repository therefore does **not** rely on one exact cron event.

### Primary publication window

The primary schedule is **07:53, 08:07, 08:21, 08:35, 08:49, and 09:03 Beijing/Singapore time**.

The 07:53 opportunity intentionally starts before AIHOT's usual 08:00 publication. If the daily snapshot is not available yet, a primary-window run polls the v1 endpoint every **15 seconds**, up to 40 attempts, so a normally-triggered runner can save the report very shortly after AIHOT publishes it.

Each later primary slot is an independent recovery opportunity in case an earlier GitHub scheduled event was delayed or dropped.

### Same-day recovery slots

Additional recovery opportunities run at **10:13, 11:25, 13:19, 14:31, 20:17, and 23:23 Beijing/Singapore time**.

These are normally very cheap no-ops because a scheduled run always checks the latest `main` first. If both files for today's Beijing date already exist, the workflow exits before contacting AIHOT. If the snapshot is still missing, a late or delayed run performs a shorter bounded retry sequence and saves it when available.

### Per-run behavior

Every scheduled opportunity:

1. checks out the latest `main` at job start, not the stale commit that happened to exist when GitHub queued the event;
2. checks whether both files for today's Beijing date already exist;
3. becomes a no-op if the complete snapshot is already committed;
4. uses dense 15-second polling before 09:15 local time and short recovery retries afterward;
5. commits with a rebase-before-push so delayed collectors do not collide with other repository writers.

The workflow timeout is **11 minutes**. The final pre-GitHub-Trending AI Daily slot is 09:03; with the repository's 15-minute planning buffer, it reserves through 09:29, before GitHub Trending starts at 09:31. Later recovery slots are deliberately placed in gaps between the other recurring collectors.

The workflow can also be run manually with a `YYYY-MM-DD` date to backfill one report. Manual runs do not use the scheduled-run early-exit shortcut, so the collector still performs its normal byte-identity validation against an existing snapshot.

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
7. Do not reduce AI Daily back to one scheduled trigger; punctual collection and same-day autonomous recovery are durable requirements.

## Files

- `ai-daily/fetch_aihot_daily.py` — fetch, validate, retry, and save both original response bodies.
- `.github/workflows/ai-daily.yml` — scheduled/manual GitHub Action.
- `ai-daily/data/` — immutable daily snapshots.
