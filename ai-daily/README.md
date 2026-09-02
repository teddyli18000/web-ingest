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

Workflows:

- `.github/workflows/ai-daily-warm.yml` — primary warm runner before publication.
- `.github/workflows/ai-daily.yml` — short recovery slots and manual backfill.

A known downstream GPT automation checks the completed GitHub mirror first at **08:15 Asia/Singapore**, then retries hourly at **09:15, 10:15, 11:15, and 12:15**. The primary objective is therefore to have both raw mirror files committed to `main` before 08:15 whenever AIHOT publishes on its normal schedule.

### Warm-runner strategy

The primary schedule is **07:21 Asia/Singapore / Beijing time**.

The goal is to acquire a GitHub-hosted runner before the expected 08:00 publication instead of depending on GitHub to dispatch a new scheduled event exactly around publication time. Once the warm runner starts:

1. it checks out the latest `main` and exits immediately if today's complete snapshot already exists;
2. if it starts before **07:58**, it deliberately stays alive and sleeps until 07:58;
3. from 07:58 until **08:16**, it polls AIHOT every **10 seconds**;
4. if GitHub dispatches the nominal 07:21 event only after 08:16, the same run skips the wait and performs a short bounded recovery fetch instead;
5. after a successful fetch it commits both raw files with a rebase-before-push.

The warm workflow has a **65-minute timeout**. On a normal day it occupies a runner for roughly 40 minutes, most of which is an intentional idle hold before publication. This is a reliability tradeoff: the repository is public, so useful Actions time is not treated as scarce private-runner budget, while obtaining a runner before 08:00 materially reduces exposure to scheduler dispatch lag near the publication deadline.

The warm run records the triggering cron, actual runner-acquisition time, planned first-fetch time, and run URL in the Step Summary.

### Why this replaced distributed early probes

On **2026-09-02**, AIHOT had generated the report by **08:00:31** local time, while GitHub showed no actual AI Daily scheduled runner until **09:27:24**. Once a runner existed, the collector fetched and committed the report within seconds. The available metadata does not identify which nominal cron produced that delayed run, so the incident demonstrates a scheduler-dispatch gap rather than a proven exact delay for one particular cron.

The previous design spread many cheap one-shot cron opportunities across the morning and hoped that at least one delayed event would land near publication. The warm-runner design is more direct: acquire one runner moderately early and keep it alive across the publication boundary.

### Recovery slots

If the warm run does not produce a snapshot, `.github/workflows/ai-daily.yml` provides short recovery opportunities at **08:43, 09:03, 10:11, and 11:27 Asia/Singapore / Beijing time**.

The first recovery starts after the warm workflow's declared timeout plus the repository's 15-minute planning buffer. Later slots feed the remaining downstream retry window. Each recovery first checks the latest `main`; once a complete snapshot exists, delayed duplicates become fast no-ops.

The warm and recovery workflows share the same `ai-daily-aihot` concurrency group, so they do not write the task concurrently even if GitHub dispatches delayed runs out of order.

### Manual backfill

`.github/workflows/ai-daily.yml` can be run manually with a `YYYY-MM-DD` Beijing date to backfill one report. Manual backfills still use the collector's byte-identity checks and never silently rewrite a different existing snapshot.

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
2. Read both `.github/workflows/ai-daily-warm.yml` and `.github/workflows/ai-daily.yml`, plus `ai-daily/fetch_aihot_daily.py`, before editing scheduling behavior.
3. Preserve both raw outputs: webpage HTML and REST API v1 JSON.
4. Preserve byte-for-byte mirroring unless the repository owner explicitly changes it.
5. Keep the API contract, warm-run timing, recovery timing, output paths, and backfill behavior documented here when they change.
6. Do not move Gmail sending, summarization, or downstream archive logic into this repository.
7. Preserve the warm-runner principle unless there is evidence that another strategy is more reliable: acquire a runner before publication and keep it alive across the expected publication boundary.
8. Keep recovery attempts bounded and inside the downstream retry window.

## Files

- `ai-daily/fetch_aihot_daily.py` — fetch, validate, retry, and save both original response bodies.
- `.github/workflows/ai-daily-warm.yml` — primary scheduled warm runner.
- `.github/workflows/ai-daily.yml` — scheduled recovery and manual backfill.
- `ai-daily/data/` — immutable daily snapshots.
