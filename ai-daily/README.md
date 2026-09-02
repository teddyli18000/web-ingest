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

- `.github/workflows/ai-daily-warm.yml` — pre-publication runner acquisition and failover ladder.
- `.github/workflows/ai-daily.yml` — short recovery slots and manual backfill.

A known downstream GPT automation checks the completed GitHub mirror first at **08:15 Asia/Singapore**, then retries hourly at **09:15, 10:15, 11:15, and 12:15**. The primary objective is therefore to have both raw mirror files committed to `main` before 08:15 whenever AIHOT publishes on its normal schedule.

GitHub scheduled Actions are best-effort and cannot provide a hard real-time dispatch guarantee. This task therefore uses repeated runner-acquisition opportunities rather than trusting one cron near 08:00.

### Warm-runner failover ladder

The warm workflow has nominal acquisition opportunities at **07:21, 07:43, 07:53, and 08:03 Asia/Singapore / Beijing time**.

All of them use the same `ai-daily-aihot` concurrency group with `cancel-in-progress: false`. GitHub therefore keeps at most one run active in the group while newer opportunities can replace an older pending opportunity. Operationally:

1. 07:21 asks GitHub for a runner early enough to absorb moderate scheduler delay.
2. If that run actually acquires a runner, it stays alive; later warm opportunities do not become parallel writers.
3. If the earlier opportunity never acquires a runner, 07:43, 07:53, and finally 08:03 provide fresh acquisition chances closer to publication.
4. Once any warm run starts before **07:57**, it deliberately holds the acquired runner until 07:57 instead of releasing it and asking GitHub for another runner near 08:00.
5. From 07:57 until **08:10**, that live runner polls AIHOT every **10 seconds**.
6. A warm run that starts after 08:10 skips the hold and makes a short immediate recovery attempt, which can still rescue the 08:15 downstream check if dispatch is only a few minutes late.
7. After a successful fetch it commits both raw files with a rebase-before-push.

The warm workflow has a **52-minute timeout**. A punctual 07:21 run can remain alive across the entire intended warm window with a small execution margin, while the later acquisition opportunities normally finish much sooner. The latest nominal 08:03 opportunity plus the repository's 15-minute planning buffer reserves AI Daily warm-run load through 09:10.

Each warm run records the triggering cron, actual runner-acquisition time, planned first-fetch time, warm deadline, and run URL in the Step Summary. This makes it possible to tell whether a failure was caused by source publication, network/fetching, or GitHub scheduler dispatch.

### Why the ladder exists

On **2026-09-02**, AIHOT had generated the report by **08:00:31** local time, while GitHub showed no actual AI Daily scheduled runner until **09:27:24**. Once a runner existed, the collector fetched and committed the report within seconds. The available metadata does not identify which nominal cron produced that delayed run, so the incident demonstrates a scheduler-dispatch gap rather than a proven exact delay for one particular cron.

A single warm cron reduces exposure to delays near 08:00 but still has one acquisition failure point. The failover ladder keeps the useful property of an already-acquired runner while adding several later chances if the earlier scheduled event never becomes an executing job.

### Recovery slots

If the warm ladder still does not produce a snapshot, `.github/workflows/ai-daily.yml` provides deliberately short recovery opportunities at **09:11, 10:11, 11:13, and 11:37 Asia/Singapore / Beijing time**.

These are one-minute-scale fetch jobs rather than another long warm hold. Each scheduled recovery makes up to two fetch attempts 10 seconds apart and has a **3-minute timeout**. The first three opportunities sit immediately before the downstream 09:15, 10:15, and 11:15 retries. The 11:37 slot is the final useful chance before the 12:15 consumer retry while still staying clear of the repository's later recurring workload.

Warm and recovery runs share the same `ai-daily-aihot` concurrency group, so delayed runs do not write AI Daily concurrently. Once a complete snapshot exists, later scheduled runs check the latest `main` and become fast no-ops.

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
5. Keep the API contract, warm acquisition ladder, recovery timing, output paths, and backfill behavior documented here when they change.
6. Do not move Gmail sending, summarization, or downstream archive logic into this repository.
7. Preserve the warm-runner principle unless evidence supports a better strategy: once a runner is acquired before publication, keep it alive instead of releasing it and depending on another near-deadline dispatch.
8. Preserve multiple acquisition opportunities; do not collapse the task back to one scheduled warm trigger.
9. Keep recovery attempts short and inside the downstream retry window.

## Files

- `ai-daily/fetch_aihot_daily.py` — fetch, validate, retry, and save both original response bodies.
- `.github/workflows/ai-daily-warm.yml` — scheduled warm-runner acquisition ladder.
- `.github/workflows/ai-daily.yml` — scheduled recovery and manual backfill.
- `ai-daily/data/` — immutable daily snapshots.
