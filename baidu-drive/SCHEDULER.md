# Baidu Drive Scheduler

This is the durable scheduler/recovery contract for moving public Baidu Netdisk shares to Google Drive through GitHub Actions.

## First principles

1. GitHub-hosted VMs are disposable.
2. Tool-owned Baidu staging is the durable readable source.
3. Google Drive's verified object/resumable state is the durable writable truth.
4. Repository state is a public checkpoint and coordination record, not authority over contradictory remote evidence.
5. There is one master scheduler. File workers execute leases; they do not make global scheduling decisions.

## One normal byte path

For every non-empty file:

```text
Baidu staged file
    ↓ exact HTTP Range
bounded response-body stream
    ↓ exact Drive resumable PUT
Google Drive
```

The configured 512 MiB value is a network byte window, not a local file or in-memory allocation. HTTP transport buffers remain bounded independently of window size.

Baidu source authorization now uses the signed `locatedownload` endpoint. Its returned CDN link is read through consecutive exact 4 MiB HTTP Ranges, exposed as one continuous stream to each 512 MiB Drive PUT. The source does not materialize 4 MiB segments on disk or change the Drive checkpoint quantum.

Small files naturally finish in one final window. Large files use many fixed-size non-final windows. Non-final Drive windows remain multiples of 256 KiB.

Zero-byte files are the only byte-path exception because there is no source range to read. They use an idempotent Drive create/adopt operation under the already-created task directory and still require exact destination reconciliation.

Do not introduce Release-asset staging or disk-backed chunk files without a measured failure mode that the direct relay cannot solve.

## Master scheduler

The master is `baidu-drive-worker.yml` running `prepare_worker.py` under the serialized `baidu-drive-live-state` concurrency group.

It alone may:

- restore/write the mover SQLite checkpoint;
- import independently verified file-worker results;
- authorize/run tool-owned staging cleanup;
- scan/resume a share and stage enough bounded batches to fill three independent file-worker slots;
- create/reconcile the Drive task directory tree;
- synchronize file-scoped relay records;
- decide which independent files receive leases;
- dispatch up to the global worker limit;
- project aggregate status back to the fixed Release.

A file worker never selects another file or edits task-global SQLite state.

## File scheduling policy

Initial policy:

```text
maximum active file workers = 3
relay window                 = 512 MiB
worker soft stop             = 5 h
workflow hard timeout        = 5 h 30 m
stale lease window           = 60 m
```

Among runnable files, prefer the largest remaining byte count first. The policy is deterministic and implemented in `scheduler.py`.

Parallelize independent files first:

```text
master
├── VM 1 → file A
├── VM 2 → file B
└── VM 3 → file C
```

Never lease one Drive file to two live workers. Same-file workflow concurrency is additionally keyed by task + file.

Do not add adaptive scheduling, multi-VM same-file prefetching, or speculative heuristics without measured evidence that this simple policy is the bottleneck.

## File-worker lifecycle

A file worker owns exactly one persisted lease. During one VM lifetime it repeatedly:

1. opens/recovers the file's sealed Drive resumable session;
2. asks Drive for the actual confirmed offset;
3. aligns the persisted streaming-MD5 state to that offset;
4. asks Baidu for exactly the next bounded byte range;
5. streams that response body directly into one Drive PUT;
6. records only Drive-confirmed progress and its matching MD5 state;
7. repeats until verified completion or the soft runtime boundary.

At 5 hours the worker stops starting new windows, checkpoints, releases the lease, and exits before the 5h30 workflow timeout.

## Wakeup and hard VM loss

After the relay step, a file worker dispatches `baidu-drive-worker.yml` explicitly through `workflow_dispatch` in a final `always()` step. This works with GitHub's built-in `GITHUB_TOKEN`; relying only on `workflow_run: completed` did not wake the master for Actions-token-dispatched file workers.

The master re-reads durable state instead of trusting the completed VM. The `workflow_run: completed` trigger remains as a possible additional entry point, but is not relied on for normal chained operation. If a VM disappears before its final step, the lease remains safe and can be reclaimed after staleness when the master next runs.

No cron watchdog and no second scheduler are used.

## Cross-VM offset and hash recovery

A VM owns no durable payload bytes.

Example:

```text
repo checkpoint: 12.0 GiB
Drive status:    12.5 GiB
```

The replacement aligns its hash state to 12.5 GiB and requests Baidu beginning at 12.5 GiB. If Drive proves less progress than a stale optimistic repo hint, the worker may rebuild the MD5 prefix from Baidu and move the checkpoint backward to the proven Drive offset.

A failed PUT may have committed none, some, or all of the request. Never infer progress from bytes read or written locally; query Drive.

## Resumable-session persistence

The Drive resumable-session URI is a capability and must never be plaintext in this public repo.

The implementation seals it with AES-256-GCM:

- one future Actions secret supplies a 32-byte master key;
- a fresh nonce is used for every seal;
- AAD binds ciphertext to the task ID and file ID;
- Git stores only the versioned sealed string.

This is intentionally narrow. Do not build a general secret database.

## Expired-session recovery

A 404 from a resumable session is not followed by blind replay.

The same file worker queries the exact destination parent + filename:

1. **One matching object:** require expected size and canonical Drive MD5, then re-read/hash the Baidu staged source and adopt only if the MD5 matches. If a canonical Baidu MD5 is present, it must match too.
2. **No object:** the expired partial session is no longer usable; clear only session-scoped offset/hash state and start a fresh resumable session from byte zero.
3. **Multiple/conflicting objects:** preserve evidence and enter `BLOCKED_RECONCILE`.
4. **Reconciliation transport/auth failure:** retry or block on auth; do not invent a destination result.

This keeps replay automatic in the safe case without risking duplicate Drive objects.

## Batch lifecycle

The master fills the three file-worker slots by staging up to three bounded batches per preparation run, stopping as soon as at least three unverified staged files are available. New batches may be staged while an earlier batch is still uploading; each batch keeps the 8 GiB planning target and may isolate one larger file. There is no duplicate staging or concurrent staging writer.

When a staged batch's files are all independently verified on Drive, the next master run imports the results into SQLite. Existing mover cleanup gates then verify provenance and remove only that registered tool-owned Baidu staging batch. Completed/active files retain their original Drive sessions and leases.

Task completion requires all manifest files to be verified and all tool-owned Baidu staging cleanup to reconcile cleanly.

Drive destination objects are never cleanup targets.

## Public state

Task-level:

```text
baidu-drive/state/runtime.json
baidu-drive/state/tasks/<task-id>.json
baidu-drive/state/checkpoints/<task-id>.sqlite.zlib.b64
```

File-level:

```text
baidu-drive/state/files/<task-id>/<file-id>.json
```

File state may contain public share metadata, source size/hash, staging identity, Drive parent/verified ID, lease/heartbeat, confirmed byte offset, serialized MD5 state, and encrypted session capability.

State writes should represent semantic changes. Avoid timestamp-only commits.

## Current implementation boundary

Implemented:

- Release control plane;
- single serialized master scheduler;
- deterministic 3-file scheduling and file leases;
- scan/stage/Drive-tree/cleanup prepare bridge;
- exact bounded Baidu Range reads;
- Drive resumable-session creation/status/upload;
- direct stream relay;
- authenticated pinned Baidu Cookie client for share/stage/download/cleanup; no developer OAuth app;
- cross-VM MD5 checkpoints;
- AES-GCM session sealing;
- zero-byte create/adopt;
- expired-session destination reconciliation;
- workflow-completion wakeup after disposable workers.

Pending for live operation:

- one-time Baidu Chrome browser login and Google rclone authorization through `AUTHORIZATION.md`;
- live API entitlement and real-provider acceptance covering cross-VM resume, session refresh/expiry, parallel files, zero-byte files and cleanup.
