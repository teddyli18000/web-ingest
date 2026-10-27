# Baidu -> Google Drive

`baidu-drive` is a Release-controlled GitHub Actions task for moving **public Baidu Netdisk shares** into Google Drive.

The fixed Release is the human control surface. The scheduler owns orchestration. GitHub-hosted VMs are disposable data pumps and must not own durable bytes or credentials.

## Current status

Implemented:

- fixed Release control plane;
- serialized control-state reconciliation;
- durable public task/checkpoint state;
- headless bridge to the pinned standalone mover;
- deterministic scheduler policy with tests.

Still intentionally pending before live transfer:

- bounded Baidu Range -> Drive resumable relay;
- per-file worker state and parallel dispatch;
- encrypted resumable-session persistence;
- authentication provisioning;
- live cross-VM acceptance tests.

Until authentication is configured, accepted tasks still fail closed at `BLOCKED_AUTH_SETUP`.

## Fixed Release

Tag: `baidu-drive-live`  
Title: `Baidu -> Google Drive`

Only edit:

```text
command: none
share_url: -
extraction_code: -
```

Commands:

- `start` — accept a new public Baidu share;
- `retry` — retry the current retryable task;
- `cancel` — cancel the current non-terminal task;
- `none` — no request.

Every non-`none` command is consumed back to `none`, including rejected commands. Bot-authored Release edits do not recursively trigger the writer.

Example:

```text
command: start
share_url: https://pan.baidu.com/s/...
extraction_code: abcd
```

The Release is only a public control/status projection. It is not a secret store, database, or normal file-transfer staging area.

## Architecture

The target architecture is deliberately small:

```text
Release baidu-drive-live
        ↓
single scheduler
        ↓
up to 3 independent file workers
        ↓
Baidu HTTP Range
        ↓
bounded runner buffer
        ↓
Google Drive resumable upload
        ↓
independent Drive verification
        ↓
tool-owned Baidu staging cleanup
```

A small file is one relay chunk. A large file is many chunks through the same path. The runner never needs to hold the complete large file.

See [`SCHEDULER.md`](SCHEDULER.md) for the durable scheduler/recovery contract.

## Scheduling principles

The scheduler is the only global decision maker. Workers execute one assigned file and do not choose their own work.

Initial policy:

```text
max active file workers: 3
relay chunk target:      512 MiB
runner disk reserve:     4 GiB
worker soft stop:        5 h
workflow hard target:    5 h 30 m
stale heartbeat window:  60 m
```

Independent files are scheduled longest-remaining-first to reduce the final long tail.

The same Drive file is never actively written by multiple VMs. If a worker disappears, a replacement first asks Drive for the actual confirmed offset and resumes Baidu from that byte. Verified remote truth wins over the repository checkpoint.

Release assets are not part of the normal transfer path. Baidu staging already provides the durable source copy, so adding GitHub as a second data staging service would add transfers and lifecycle complexity without required durability.

## Durable state

The existing task-level state is under:

```text
baidu-drive/state/
├── runtime.json
├── tasks/
└── checkpoints/
```

The relay scheduler will extend durable state with per-file progress rather than putting large bytes in Git.

Public state may contain public-share metadata, file size/hash, tool-owned staging identity, status, byte offset, and safe Drive identifiers.

Sensitive capability state must never be plaintext in this public repository. In particular, Google resumable-session URIs will be authenticated-encrypted before persistence; only ciphertext is committed.

A VM must be replaceable without copying its local filesystem.

## Transfer core

The current bridge still reuses:

```text
teddyli18000/baidu-drive-mover
f4ca661d367aa2a067344efa989f0bfc95b64618
```

The current mover pipeline is:

```text
share scan
  -> tool-owned Baidu staging
  -> bounded local cache
  -> Drive upload
  -> Drive ID + size + MD5 verification
  -> cleanup
```

That bridge remains useful for scan/staging/recovery while the data path is upgraded from full-file local cache transfer to bounded Range/resumable relay.

The standalone mover pin or bridge contract must not change without passing the repository integration gate and updating this documentation.

## Cross-VM recovery

For data relay, the durable progress value is the byte offset Google Drive has actually confirmed.

Example:

```text
repo says:   12.0 GiB
Drive says:  12.5 GiB
```

The next VM resumes from **12.5 GiB**.

It then asks Baidu for a bounded range beginning at that byte and advances Drive from the same offset. Local chunks are disposable and are removed after remote confirmation.

This means VM replacement does not require preserving `.part` files.

## Authentication boundary

Authentication remains intentionally separate from public task state.

The current worker recognizes runner-local prepared files:

```text
BAIDU_DRIVE_BAIDU_AUTH_FILE
BAIDU_DRIVE_RCLONE_CONFIG_FILE
BAIDU_DRIVE_RCLONE_BIN
BAIDU_DRIVE_BRIDGE_BIN
```

These are internal path interfaces, not a final choice of credential mechanism.

The final authentication layer must:

- provision credentials only inside the ephemeral runner;
- never echo them;
- never persist plaintext tokens/cookies/session URLs in Git, Release bodies, artifacts, or summaries;
- support non-interactive refresh/recovery suitable for bot operation.

Until that is wired, the worker must remain fail-closed.

## Workflows

### `baidu-drive-reconcile.yml`

Owns the Release protocol and control-plane task state. It validates code changes and dispatches work only after proving a `start` or `retry` request was accepted.

### `baidu-drive-worker.yml`

Current serialized transfer adapter. It remains the fail-closed execution entry point while the per-file relay/scheduler worker is built.

Control-plane serialization and data-plane parallelism are intentionally different concerns: the final scheduler will keep global decisions serialized while independent file workers execute concurrently.

## Safety invariants

- Only public Baidu shares belong here.
- Google Drive destination objects are never cleanup targets.
- Cleanup may remove only durably registered tool-owned local/Baidu staging.
- A file is complete only after independent Drive verification.
- Remote mutations must be idempotent/reconcilable.
- The repository checkpoint is not allowed to override proven remote state.
- No credential, cookie, OAuth token, private header, signed URL, resumable-session URI, or private-source data may be committed in plaintext.

## Validation

```bash
python3 -m py_compile baidu-drive/*.py
python3 -m unittest discover -s baidu-drive/tests -v
python3 tools/check-repository-integrity.py
```

`repository-integrity.yml` additionally checks out the pinned mover core, runs relevant Go tests, and compiles the Linux Actions bridge.
