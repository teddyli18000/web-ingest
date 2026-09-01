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

This collector is designed to run without an Agent watching it. GitHub scheduled workflow events are best-effort, so the repository does **not** rely on one exact cron event.

A known downstream GPT automation checks the completed GitHub mirror first at **08:15 Asia/Singapore**, then retries hourly at **09:15, 10:15, 11:15, and 12:15**. The collector therefore optimizes for one operational objective: have both raw mirror files committed to `main` before 08:15 whenever AIHOT publishes on its normal schedule. Recovery work after the downstream retry window is intentionally avoided.

### Primary publication window

The primary schedule is **07:51, 07:57, 08:03, 08:09, and 08:13 Beijing/Singapore time**.

The 07:51 opportunity starts before AIHOT's usual 08:00 publication. Any scheduled run that actually begins before 08:15 polls the v1 endpoint every **10 seconds**, up to 70 attempts. This keeps a runner warm around publication and makes the first downstream 08:15 check likely to see a complete committed snapshot rather than waiting for a later retry.

The other primary slots are independent GitHub schedule events. They exist because one scheduled event can be delayed or dropped; they are not intended to create duplicate snapshots. Top-level concurrency serializes actual execution and every run first checks the latest `main`.

### Recovery slots

If the 08:15 consumer check has already passed and the snapshot is still missing, bounded recovery opportunities run at **08:29, 09:03, 10:11, and 11:27 Beijing/Singapore time**.

These slots are chosen to feed the remaining downstream retry window while still respecting the repository's cross-workflow schedule guard. There are no AI Daily recovery schedules after the last useful window leading into the downstream 12:15 check.

### Per-run behavior

Every scheduled opportunity:

1. checks out the latest `main` at job start, not the stale commit that happened to exist when GitHub queued the event;
2. checks whether both files for today's Beijing date already exist;
3. becomes a no-op if the complete snapshot is already committed;
4. uses dense 10-second polling when it begins before 08:15 local time;
5. uses only short bounded retries after 08:15;
6. commits with a rebase-before-push so delayed collectors do not collide with other repository writers.

The workflow timeout is **13 minutes**. With the repository's 15-minute planning buffer, the 09:03 slot reserves through 09:31, the 10:11 slot through 10:39, and the 11:27 slot through 11:55; these boundaries remain compatible with the other recurring collectors under the schedule guard.

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
7. Do not reduce AI Daily back to one scheduled trigger; punctual collection before the first downstream check is the durable priority.
8. Do not add recovery schedules after the downstream retry window unless that downstream contract changes.

## Files

- `ai-daily/fetch_aihot_daily.py` — fetch, validate, retry, and save both original response bodies.
- `.github/workflows/ai-daily.yml` — scheduled/manual GitHub Action.
- `ai-daily/data/` — immutable daily snapshots.
