# AI Daily

Collect the daily report published by **AIHOT**.

## Source

- Site: `https://aihot.virxact.com/`
- REST API v1: `GET https://aihot.virxact.com/api/v1/dailies/latest`
- Date-specific REST API v1: `GET https://aihot.virxact.com/api/v1/dailies/{date}`
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

The primary objective is to have both raw mirror files committed to `main` before 08:15 whenever AIHOT publishes on its normal schedule, then hand the completed date immediately to the downstream archive workflow. Downstream scheduled retries remain fallback behavior; they are no longer the preferred transport path once the active handoff succeeds.

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
2. if it starts before **07:59:45**, it deliberately holds the acquired runner until 07:59:45;
3. from 07:59:45 through **08:14**, it polls AIHOT every **5 seconds** with a **5-second per-request timeout**;
4. if it starts after 08:14, it skips the hold and performs a short immediate recovery fetch;
5. after a successful fetch it commits both raw files with a rebase-before-push;
6. after the push succeeds it confirms both public raw files are readable and dispatches the fixed downstream archive workflow;
7. if the entire warm publication window ends without a complete snapshot, or if post-push handoff fails, the workflow fails instead of reporting a misleading green success.

The warm job has a **230-minute timeout**. A punctual 04:37 runner can stay alive through the publication window, while that early start gives the scheduler several hours of delay budget. The 05:07 fallback still reaches the publication window under delays comparable to the worst observed on 2026-09-03.

Each scheduled warm run records its triggering cron, actual runner-acquisition time, planned first-fetch time, warm deadline, and run URL in the Step Summary.

This is an intentional exception to the repository's normal preference against long idle Actions: punctuality is the task requirement, the repository is public, and holding a runner already acquired is materially more reliable than asking GitHub for a new runner close to 08:00.

### Low-latency publication watch

The live collector resolves the current Beijing date once it starts and polls **`/api/v1/dailies/{date}` directly**, rather than waiting for `/api/v1/dailies/latest` to advance from yesterday. The date-specific endpoint is the authoritative live target for this task because its URL already names the report we are waiting for.

The collector also sends standard `Cache-Control: no-cache` / `Pragma: no-cache` request headers so intermediaries are asked to revalidate freshness. It does **not** add undocumented query-string cache busters.

Live-mode response handling is deliberately publication-aware:

- HTTP 404 from either the date-specific API or its daily webpage is treated as "not published yet" and retried within the warm window.
- The API must report exactly the expected date, schema version, sections shape, and canonical daily page URL before the snapshot is accepted.
- The HTML page must be valid UTF-8 HTML and contain the expected report date before either raw response is persisted.
- HTTP 429 obeys `Retry-After` when supplied.
- 5xx, network errors, and request timeouts use bounded exponential retry delays rather than tight failure loops.
- Manual historical backfills keep stricter semantics: a 404 for an explicitly requested past date is a hard failure, not "not ready".

The API response and webpage are both fetched and validated **before** either file is written, so a temporary page lag cannot leave a network-induced half-snapshot. Existing files remain byte-identity protected.

### Recovery slots

If the warm runner still does not produce a snapshot, `.github/workflows/ai-daily.yml` provides short recovery opportunities at **09:13, 10:13, 11:13, and 11:37** local time.

Each scheduled recovery makes up to two fetch attempts 10 seconds apart and has a **3-minute timeout**. Recovery HTTP requests are individually bounded to 10 seconds. The first three sit immediately before useful downstream retry windows. The 11:37 slot is the final useful chance while remaining clear of later repository workload.

Warm and recovery workflows share the same concurrency group, so delayed runs do not write AI Daily concurrently. Once a complete snapshot exists, later normal runs become fast no-ops.

If a run successfully pushed the snapshot but then failed during the post-push handoff, rerunning that **same failed Actions run** is allowed to retry handoff against the already-present snapshot. Ordinary later scheduled runs do not deliberately dispatch the same completed day again.

### Manual backfill

`.github/workflows/ai-daily.yml` can be run manually with a `YYYY-MM-DD` Beijing date. Manual backfills retain byte-identity checks, use the date-specific v1 endpoint, and never silently rewrite a different existing snapshot.

Manual historical backfills do **not** automatically trigger the downstream mail/archive chain. The automatic handoff is for the scheduled live daily production path only.

### Downstream archive handoff

The active production handoff is intentionally narrow and ends after a successful `workflow_dispatch` request.

After a scheduled live run creates a new snapshot:

1. both source responses have already passed the normal API/HTML consistency validation;
2. the snapshot commit must succeed;
3. `git push origin HEAD:main` must succeed;
4. only then does the workflow check the public `raw.githubusercontent.com` URLs for both `aihot-daily.html` and `aihot-daily.json`;
5. both raw files must return HTTP 200 before dispatch;
6. the workflow then sends exactly one fixed GitHub REST request to `teddyli18000/Github_test`, workflow `ai-daily-archive.yml`, ref `master`, with only `inputs.date` set to the successfully generated report date;
7. only HTTP **204** counts as a successful handoff.

Raw visibility checking is bounded to at most 12 attempts and approximately one minute. If the pushed files do not become publicly readable in that window, the source workflow fails and does not dispatch downstream.

The handoff implementation is `ai-daily/trigger_github_test_archive.py`. Its repository, workflow, ref, API URL, and raw source base are constants, not caller-controlled parameters. The only runtime argument is the validated report date.

Authentication is only through the Actions secret `AI_DAILY_DISPATCH_TOKEN`. Do not place the token in source, repository variables, artifacts, logs, `.env` files, or any other persisted material. The workflow exposes the secret only as the environment variable of the handoff step.

Dispatch normally runs once. A single short retry is permitted only for GitHub HTTP 500 / 502 / 503 / 504 responses. Authentication, permission, repository, workflow, ref, or input errors such as 401 / 403 / 404 / 422 fail immediately.

This repository does not archive the report, trigger Bot 2 directly, send Agent Mail, or poll `Github_test` for downstream completion as part of normal production.

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
2. Read both `.github/workflows/ai-daily-warm.yml` and `.github/workflows/ai-daily.yml`, plus `ai-daily/fetch_aihot_daily.py` and `ai-daily/trigger_github_test_archive.py`, before editing scheduling or handoff behavior.
3. Preserve both raw outputs: webpage HTML and REST API v1 JSON.
4. Preserve byte-for-byte mirroring unless the repository owner explicitly changes it.
5. Keep the API contract, warm acquisition timing, publication polling behavior, recovery timing, output paths, and handoff behavior documented here when they change.
6. Do not move Gmail sending, summarization, downstream archive logic, or Bot 2 logic into this repository.
7. Preserve the early-warm principle unless evidence supports a better mechanism: acquire a runner well before publication and keep it alive across 08:00.
8. Do not move the primary warm acquisition back near 08:00 merely to reduce runner time; GitHub scheduler delay has already caused repeated missed 08:15 deadlines.
9. Keep the live publication watch date-specific, bounded, and failure-visible; do not silently turn an exhausted warm window into success.
10. Keep the archive handoff fixed-capability: fixed repository/workflow/ref, only the validated report date as input, and only after a successful push.
11. Keep recovery attempts short and inside useful downstream retry windows.

## Files

- `ai-daily/fetch_aihot_daily.py` — fetch, validate, retry, and save both original response bodies.
- `ai-daily/trigger_github_test_archive.py` — post-push raw visibility check and fixed Bot 1 dispatch.
- `.github/workflows/ai-daily-warm.yml` — early warm runner, low-latency publication watch, and primary handoff.
- `.github/workflows/ai-daily.yml` — scheduled recovery, recovery handoff, and manual backfill.
- `ai-daily/data/` — immutable daily snapshots.
