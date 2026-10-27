# Baidu -> Google Drive

`baidu-drive` is a Release-controlled GitHub Actions task for moving **public Baidu Netdisk shares** into Google Drive.

The fixed Release is the human control/status surface. One serialized master scheduler owns all global decisions. GitHub-hosted VMs are disposable data pumps and must not own durable bytes or credentials.

## Current status

Implemented:

- fixed Release control plane and accepted-command dispatch;
- durable task/SQLite checkpoints and file-scoped relay state;
- scan, isolated Baidu staging, Drive tree creation, verified-result import, and guarded cleanup through the pinned mover core;
- exact bounded Baidu byte ranges;
- direct Baidu response-body -> Google Drive resumable streaming;
- 512 MiB network windows without whole-file or whole-chunk disk buffering;
- up to three independent file workers with file-scoped leases;
- cross-VM Drive offset and streaming-MD5 recovery;
- AES-256-GCM sealing of resumable-session URIs, bound to task + file identity;
- zero-byte Drive file creation/adoption with exact destination reconciliation;
- expired-session reconciliation before any replay;
- automatic master-scheduler wakeup whenever a file-worker workflow completes, including failed/cancelled runs.

Still intentionally pending before live transfer:

- final Baidu and Google authentication provisioning in Actions;
- live cross-VM acceptance against real provider accounts.

Until authentication is configured, accepted tasks fail closed at `BLOCKED_AUTH_SETUP`.

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

The Release is only a public control/status projection. It is not a secret store, database, or file-transfer staging area.

## Architecture

```text
Release baidu-drive-live
        ↓
Reconcile
        ↓
master scheduler / prepare worker
        ├─ scan / stage / Drive tree / cleanup
        └─ lease up to 3 independent files
                 ↓
            file workers
                 ↓
       Baidu exact HTTP Range
                 ↓ direct stream
       Drive resumable upload
                 ↓
       remote offset + MD5 proof
                 ↓
      verified result -> master
```

There is no separate small-file engine. A small non-empty file is one final relay window; a large file uses many fixed-size windows through the same path. Zero-byte files use a minimal Drive create/adopt branch because there are no source bytes to range-read.

A 512 MiB relay window is a **network byte interval**, not a 512 MiB local file. HTTP buffers stay small and bounded, so runner disk capacity does not set the maximum transferable file size.

Release assets are not part of the normal transfer path. Baidu staging is already the durable source copy.

See [`SCHEDULER.md`](SCHEDULER.md) for the durable scheduling/recovery contract.

## Scheduling

Initial policy:

```text
max active file workers: 3
relay window target:     512 MiB
worker soft stop:        5 h
workflow hard timeout:   5 h 30 m
stale lease window:      60 m
```

The master scheduler is the only global decision maker. It prefers independent files with the largest remaining byte count and never assigns two live workers to the same Drive file.

Each file worker owns one persisted lease and may process many relay windows during the same VM lifetime. At the soft runtime boundary it checkpoints and releases the lease instead of trying to run until GitHub's hard limit.

`baidu-drive-worker.yml` is also triggered by completion of `Baidu Drive File Worker`. This is the hard-runner-loss wakeup path: GitHub completing a worker workflow wakes the same master scheduler, which re-reads current durable state and reclaims stale work when eligible. No polling/cron watchdog and no second scheduler are used.

## Cross-VM recovery

For an active resumable session, Drive's observed offset is authoritative. The repo checkpoint is only a recovery hint.

```text
repo checkpoint:  12.0 GiB
Drive says:       12.5 GiB
next Baidu range: starts at 12.5 GiB
```

Streaming MD5 state is persisted at exactly the same confirmed offset. If Drive proves an offset different from the checkpoint, the worker rebuilds/catches up the hash only for bytes needed to align with Drive truth.

A resumable-session URI is capability-bearing state. It is persisted only as AES-256-GCM ciphertext using AAD derived from the task ID and file ID. The future Actions secret provides the 32-byte master key; Git stores only the sealed value.

If a Drive resumable session expires, the file worker does **not** blindly create a new file. It first lists the exact task-root parent/name:

- one object with matching size and source-verified MD5 -> adopt it as completed;
- no object -> discard the expired session's partial progress and safely start again from byte zero;
- duplicate/conflicting object -> enter `BLOCKED_RECONCILE` rather than risk a duplicate or overwrite.

## Durable state

```text
baidu-drive/state/
├── runtime.json
├── tasks/
├── checkpoints/
└── files/<task-id>/<file-id>.json
```

Public file state may include public-share metadata, tool-owned Baidu staging identity, size/hash, status, confirmed offset, serialized MD5 checkpoint, heartbeat/lease metadata, and safe Drive IDs.

Credentials, access/refresh tokens, cookies, private headers, and plaintext resumable-session URIs must never enter Git, Release text, Actions summaries, or artifacts.

## Transfer core

The Actions adapters are compiled against the pinned standalone mover commit:

```text
teddyli18000/baidu-drive-mover
a9e76feb18fe9ca1ac680d0ea555aac684d622de
```

That revision supplies the hardened scanner/stager/state/Drive-tree/cleanup logic plus the exact bounded Baidu range primitive. Task-local Go adapters under `baidu-drive/mover/` add the Actions-specific prepare and direct-relay paths without changing the standalone Windows CLI's normal cache-based behavior.

The pin or bridge contract must not change without passing the repository integration gate and updating this documentation.

## Authentication boundary

Authentication remains intentionally separate from public task state.

Prepare/master path expects future runner-local inputs:

```text
BAIDU_DRIVE_BAIDU_AUTH_FILE
BAIDU_DRIVE_RCLONE_CONFIG_FILE
BAIDU_DRIVE_RCLONE_BIN
```

File-relay path expects future runner-local inputs:

```text
BAIDU_DRIVE_BAIDU_AUTH_FILE
BAIDU_DRIVE_GOOGLE_ACCESS_TOKEN_FILE
BAIDU_DRIVE_STATE_KEY_FILE
```

The build itself supplies the prepare/relay binaries. These path interfaces do not prescribe the final OAuth/Secret provisioning mechanism.

The final auth layer must provision credentials only inside the ephemeral runner, never echo them, and support non-interactive refresh/recovery suitable for unattended bot operation.

## Workflows

### `baidu-drive-reconcile.yml`

Owns Release protocol and task-level control state. It dispatches the master scheduler only after proving a `start` or `retry` command was accepted.

### `baidu-drive-worker.yml`

The **single master scheduler**. It serializes SQLite/control mutations, imports verified file results, performs guarded cleanup, prepares the next staging batch, creates/reconciles the Drive directory tree, and fills free file-worker slots. It also wakes on every file-worker workflow completion.

### `baidu-drive-file-worker.yml`

One disposable VM for one leased file. Different files may run concurrently; the same task/file pair has its own concurrency key and cannot overlap itself.

## Safety invariants

- Only public Baidu shares belong here.
- VM-local bytes are disposable.
- Google Drive destination objects are never cleanup targets.
- Cleanup removes only durably registered tool-owned Baidu staging after destination verification.
- A file is complete only after Drive ID + size + MD5 are independently reconciled against the streamed source.
- Remote mutations must be idempotent or preceded/followed by reconciliation sufficient to avoid blind replay.
- Proven remote state outranks stale repo hints.
- No credential, cookie, OAuth token, private header, signed URL, plaintext resumable-session URI, or private-source data may be committed.

## Validation

```bash
python3 -m py_compile baidu-drive/*.py
python3 -m unittest discover -s baidu-drive/tests -v
python3 tools/check-repository-integrity.py
```

`repository-integrity.yml` additionally checks out the pinned mover core, runs the relevant Go packages plus relay protocol tests, and compiles all Linux Actions adapters.
