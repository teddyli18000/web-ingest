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

- `.github/workflows/ai-daily-warm.yml` — early runner acquisition and publication watch.
- `.github/workflows/ai-daily.yml` — short recovery slots and manual backfill.

A known downstream GPT automation checks the completed mirror first at **08:15 Asia/Singapore**, then retries at **09:15, 10:15, 11:15, and 12:15**. The primary objective is to have both raw mirror files committed to `main` before 08:15 whenever AIHOT publishes on its normal schedule.

GitHub scheduled Actions are best-effort. Two consecutive incidents showed that near-deadline cron hedging is not enough:

- **2026-09-02:** AIHOT was ready around 08:00, but no AI Daily runner appeared until about 09:27.
- **2026-09-03:** AIHOT generated the report at **08:00:00.393** local time, while the nominal 07:21 / 07:43 / 07:53 / 08:03 warm opportunities actually appeared around **09:07 / 09:25 / 09:30 / 10:49**. The mirror was committed at about **09:07:33**.

The durable conclusion is that several nearby `schedule` events can be delayed together. Therefore the task must acquire a runner **hours before** publication and keep that runner alive across 08:00.

### Early warm acquisition

The warm workflow has two nominal acquisition opportunities:

- **04:37** Asia/Singapore / Beijing — primary early runner.
- **05:07** — fallback if the first schedule is dropped or unusually delayed.

Both use the same `ai-daily-aihot` concurrency group with `cancel-in-progress: false`. At most one run executes in the group. If an early run is already alive, the later opportunity remains only a fallback and does not become a parallel writer.

Once a warm run actually starts:

1. it checks the latest `main` and exits if today's complete snapshot already exists;
2. if it starts before **07:55**, it deliberately holds the acquired runner until 07:55;
3. from 07:55 through **08:14**, it polls AIHOT every **10 seconds**;
4. if it starts after 08:14, it skips the hold and performs a short immediate recovery fetch;
5. after a successful fetch it commits both raw files with a rebase-before-push.

The warm job has a **230-minute timeout**. A punctual 04:37 runner can stay alive through the publication window, while that early start gives the scheduler several hours of delay budget. The 05:07 fallback still reaches the publication window under delays comparable to the worst observed on 2026-09-03.

Each scheduled warm run records its triggering cron, actual runner-acquisition time, planned first-fetch time, warm deadline, and run URL in the Step Summary.

This is an intentional exception to the repository's normal preference against long idle Actions: punctuality is the task requirement, the repository is public, and holding a runner already acquired is materially more reliable than asking GitHub for a new runner close to 08:00.

### Recovery slots

If the warm runner still does not produce a snapshot, `.github/workflows/ai-daily.yml` provides short recovery opportunities at **09:13, 10:13, 11:13, and 11:37** local time.

Each scheduled recovery makes up to two fetch attempts 10 seconds apart and has a **3-minute timeout**. The first three sit immediately before the 09:15 / 10:15 / 11:15 downstream retries. The 11:37 slot is the final useful chance before 12:15 while remaining clear of later repository workload.

Warm and recovery workflows share the same concurrency group, so delayed runs do not write AI Daily concurrently. Once a complete snapshot exists, later runs become fast no-ops.

### Manual backfill

`.github/workflows/ai-daily.yml` can be run manually with a `YYYY-MM-DD` Beijing date. Manual backfills retain byte-identity checks and never silently rewrite a different existing snapshot.

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
5. Keep the API contract, warm acquisition timing, recovery timing, output paths, and backfill behavior documented here when they change.
6. Do not move Gmail sending, summarization, or downstream archive logic into this repository.
7. Preserve the early-warm principle unless evidence supports a better mechanism: acquire a runner well before publication and keep it alive across 08:00.
8. Do not move the primary warm acquisition back near 08:00 merely to reduce runner time; GitHub scheduler delay has already caused repeated missed 08:15 deadlines.
9. Keep recovery attempts short and inside the downstream retry window.

## Files

- `ai-daily/fetch_aihot_daily.py` — fetch, validate, retry, and save both original response bodies.
- `.github/workflows/ai-daily-warm.yml` — early warm runner.
- `.github/workflows/ai-daily.yml` — scheduled recovery and manual backfill.
- `ai-daily/data/` — immutable daily snapshots.
