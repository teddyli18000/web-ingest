# Baidu -> Google Drive

`baidu-drive` is a Release-controlled, GitHub Actions-backed task for moving **public Baidu Netdisk shares** into Google Drive. The task is being migrated from the standalone `baidu-drive-mover` design while preserving its resumable, verified, bounded-transfer principles.

## Current status

**Control plane ready; transfer authentication/worker intentionally not configured yet.**

The first milestone implements the durable human/bot protocol without storing credentials:

```text
fixed GitHub Release
        ↓ human edits request
reconcile Action
        ↓
repo state under baidu-drive/state/
        ↓
Release status projection
```

Until the OAuth/secret-backed worker is added, a valid `start` or `retry` request is accepted and recorded as `BLOCKED_AUTH_SETUP`. This is deliberate fail-closed behavior, not a simulated transfer.

## Fixed Release

Tag: `baidu-drive-live`  
Title: `Baidu -> Google Drive`

The workflow creates the Release automatically when the control plane first runs. The Release is public because this repository is public.

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

Every non-`none` command is consumed back to `none` after processing, even if rejected. Action-authored Release edits are ignored by the Release trigger, preventing recursion.

### Example

```text
command: start
share_url: https://pan.baidu.com/s/...
extraction_code: abcd
```

Save the Release. The reconcile Action validates the request, creates durable task state, clears the request fields, and updates the Status section.

## State model

The Release is a human control/status projection, not the database.

```text
baidu-drive/state/
├── runtime.json
└── tasks/
    └── bd-<timestamp>-<hash>.json
```

`runtime.json` stores only active/last task identity. Each task record stores public source parameters and non-secret progress/status fields. Future workers will update these files through the GitHub Contents API using optimistic blob-SHA writes.

No credentials, cookies, OAuth access/refresh tokens, private headers, signed URLs, or private source data may be written into repository state, Release text, logs, summaries, caches, or artifacts.

## Intended transfer pipeline

The standalone mover already established the desired safety model:

```text
public Baidu share scan
  -> bounded tool-owned Baidu staging
  -> bounded resumable runner cache
  -> Google Drive upload
  -> independent Drive ID + size + MD5 verification
  -> cleanup only tool-owned staging/cache
  -> completed
```

The Actions-native worker will keep the same invariants while replacing interactive Chrome/cookie authorization with non-interactive OAuth/secret-backed authorization. The exact credential layout is intentionally deferred until the owner chooses how to provision the required secrets.

## Workflow

`.github/workflows/baidu-drive-reconcile.yml` is the durable control-plane entry point.

Triggers:

- manual `workflow_dispatch`;
- human edit of Release `baidu-drive-live`;
- pushes that change the task/control-plane implementation.

All writers use concurrency group `baidu-drive-live-state` with `cancel-in-progress: false`.

The workflow uses `contents: write` only because it must create/patch the fixed Release and commit task-owned state. It does not receive or print transfer credentials in the current phase.

## Public-repository safety

Use this control surface only for source links and extraction codes that are already intended to be public. Do not paste account passwords, cookies, OAuth tokens, authorization codes, private signed download URLs, or private data into the Release.

When authentication is added, credential values must enter through GitHub Actions secrets (or another explicitly approved secret store) and must never be persisted into the repository or Release.

## Validation

```bash
python3 -m py_compile baidu-drive/controller.py
python3 -m unittest discover -s baidu-drive/tests -v
python3 tools/check-repository-integrity.py
```
