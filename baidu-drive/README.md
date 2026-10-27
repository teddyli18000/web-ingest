# Baidu -> Google Drive

`baidu-drive` is a Release-controlled, GitHub Actions-backed task for moving **public Baidu Netdisk shares** into Google Drive. It reuses the standalone `baidu-drive-mover` transfer core while adapting control, recovery, runner storage, and authentication boundaries for ephemeral GitHub-hosted runners.

## Current status

**Release control plane, serialized worker, durable checkpointing, and the headless mover bridge are implemented. Authentication provisioning is intentionally still pending.**

Current behavior is therefore fail-closed:

```text
fixed GitHub Release
        ↓ human edits request
Baidu Drive Reconcile
        ↓ accepted start/retry only
Baidu Drive Worker
        ↓ auth files missing today
BLOCKED_AUTH_SETUP
```

No real transfer is attempted until the owner explicitly chooses and configures the credential/OAuth provisioning mechanism.

## Fixed Release

Tag: `baidu-drive-live`  
Title: `Baidu -> Google Drive`

The Release is the human/bot control and status surface. It is public because this repository is public.

Only edit the request fields:

```text
command: none
share_url: -
extraction_code: -
```

Supported commands:

- `start` — create a new active task from a public Baidu share URL.
- `retry` — retry the current task only from a retryable/blocked state.
- `cancel` — cancel the current non-terminal task.
- `none` — no request.

Every non-`none` command is consumed back to `none` after processing, including rejected commands. Action-authored Release edits are ignored by the Release trigger, preventing recursion. A worker is queued only when Reconcile proves that `start` or `retry` was actually accepted; a rejected request cannot accidentally retry an older task.

### Example

```text
command: start
share_url: https://pan.baidu.com/s/...
extraction_code: abcd
```

Save the Release. Reconcile validates and consumes the request, creates durable task state, and queues the serialized worker. Until authentication provisioning is configured, that worker reports `BLOCKED_AUTH_SETUP` without attempting interactive login.

## Architecture

```text
Release baidu-drive-live
        ↓
.github/workflows/baidu-drive-reconcile.yml
        ↓ accepted request
.github/workflows/baidu-drive-worker.yml
        ↓
baidu-drive/worker.py
        ↓
headless Go bridge
        ↓
pinned baidu-drive-mover core
        ↓
Baidu staging -> bounded cache -> Drive verify -> cleanup
```

All state writers share concurrency group `baidu-drive-live-state` with `cancel-in-progress: false`, so Release projection, task state, checkpoint state, and remote mutations are serialized through one logical writer lane.

## Durable state

The Release is a status projection, not the database.

```text
baidu-drive/state/
├── runtime.json
├── tasks/
│   └── bd-<timestamp>-<hash>.json
└── checkpoints/
    └── bd-<timestamp>-<hash>.sqlite.zlib.b64
```

- `runtime.json` stores active/last task identity.
- `tasks/*.json` stores public source parameters plus non-secret progress/status fields.
- `checkpoints/*.sqlite.zlib.b64` is a compressed mover SQLite checkpoint. It may contain the manifest and transfer state for the submitted **public** share, but it must never contain account credentials, cookies, OAuth tokens, rclone configuration, signed credential-bearing URLs, private headers, or private-source data.

The SQLite checkpoint is the durable transfer state across disposable runners. Runner-local downloaded file bytes are **not** committed. On a fresh runner, bridge recovery rewinds cache-dependent pre-verification states back to `BAIDU_STAGED`, preserving any known Drive object ID so the normal mover reconciliation can redownload and safely adopt/verify a remote object that may already have committed.

## Transfer core

The bridge reuses `teddyli18000/baidu-drive-mover` at the pinned source commit:

```text
f4ca661d367aa2a067344efa989f0bfc95b64618
```

The web-ingest bridge is copied into that pinned Go module at build time so it can reuse the mover's internal packages without duplicating the pipeline implementation.

The inherited transfer invariants remain:

```text
public Baidu share scan
  -> bounded tool-owned Baidu staging
  -> bounded resumable runner cache
  -> Google Drive upload
  -> independent Drive ID + size + MD5 verification
  -> cleanup only tool-owned staging/cache
  -> completed
```

Google Drive destination objects are never cleanup targets. A file is not complete merely because an upload process returned success; the mover's independent Drive verification remains the completion gate.

## Ephemeral authentication boundary

Authentication is deliberately separated from durable task state. The worker expects prepared files only inside the ephemeral runner:

```text
BAIDU_DRIVE_BAIDU_AUTH_FILE
BAIDU_DRIVE_RCLONE_CONFIG_FILE
BAIDU_DRIVE_RCLONE_BIN
BAIDU_DRIVE_BRIDGE_BIN
```

These variables name runner-local files; they are not credential values themselves. The repository currently has **no step that provisions them**. When the owner chooses the final OAuth/secret design, preceding workflow steps may create these files from GitHub Actions secrets or another explicitly approved secret source, use them for the run, and let the runner destroy them afterward.

The bridge itself never opens an interactive browser. If the prepared Baidu session or Drive authorization is absent/expired and cannot be refreshed by the chosen future provisioning layer, the transfer stops safely for operator recovery.

## Workflows

### `baidu-drive-reconcile.yml`

Durable control-plane entry point. It wakes on:

- human edit of Release `baidu-drive-live`;
- manual `workflow_dispatch`;
- pushes that change the task/control-plane implementation.

It validates and consumes Release commands, commits non-secret task/control state, refreshes the Release status projection, and dispatches a worker only after an accepted `start` or `retry`.

### `baidu-drive-worker.yml`

Serialized transfer worker. It currently runs the state adapter and stops at `BLOCKED_AUTH_SETUP` because auth provisioning is intentionally absent. Once provisioning is added, the same adapter restores the checkpoint, invokes the Go bridge, persists the next checkpoint, updates task progress, and refreshes the Release projection.

## Public-repository safety

Use this task only for public Baidu shares whose link, extraction code, names, and manifest metadata are acceptable to persist publicly.

Never commit or expose:

- account passwords;
- Baidu account cookies/session tokens;
- OAuth access or refresh tokens;
- Google/rclone credential configuration;
- private headers;
- signed or temporary credential-bearing URLs;
- private-source data;
- secret-derived diagnostics.

Do not upload credential-containing Actions artifacts or Step Summaries. Authentication files must remain runner-local and ephemeral.

## Validation

Normal repository validation covers both the control plane and the mover bridge:

```bash
python3 -m py_compile baidu-drive/controller.py baidu-drive/worker.py
python3 -m unittest discover -s baidu-drive/tests -v
python3 tools/check-repository-integrity.py
```

`repository-integrity.yml` additionally checks out the pinned mover core, copies in `action-main.go` and `action_recovery.go`, runs the relevant mover package tests, and builds `cmd/baidu-drive-action` on Linux. A pin change is not complete until that integration gate passes.
