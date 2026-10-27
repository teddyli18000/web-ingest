# Baidu Drive Scheduler

This document is the durable design contract for the Actions scheduler that moves public Baidu Netdisk shares to Google Drive.

The design starts from four facts:

1. GitHub-hosted VMs are disposable and may disappear at any time.
2. The Baidu staging file is the durable readable source.
3. Google Drive resumable upload state is the durable writable destination state.
4. A repository checkpoint is only a recovery hint; verified remote state is authoritative.

Everything else follows from those facts.

## One data path

Do not maintain separate "small file" and "large file" transfer engines.

Every file uses the same bounded relay:

```text
Baidu staged file
    ↓ HTTP Range
bounded runner buffer
    ↓ Drive resumable upload
Google Drive
```

A small file naturally completes in one chunk. A large file uses many chunks. No complete source file has to fit on runner disk.

Release assets are not part of the normal data path. Baidu already provides the durable source copy, so uploading chunks to GitHub and downloading them again would add another transfer, another lifecycle, and another failure surface without adding required durability.

## Scheduler ownership

There is one logical scheduler. It is the only component allowed to decide what work should run next.

Workers do not choose files, split ownership, or infer global concurrency. A worker receives one file assignment and advances that file until it completes, reaches the soft runtime boundary, or hits a retryable block.

The scheduler policy is deterministic and lives in `scheduler.py`.

Initial policy:

- maximum active file workers: **3**;
- relay chunk target: **512 MiB**;
- runner disk reserve: **4 GiB**;
- worker soft stop: **5 hours**;
- workflow hard timeout target: **5 hours 30 minutes**;
- stale worker heartbeat window: **60 minutes**.

These values are safety defaults, not performance promises. Change them only from measured operating evidence.

## Parallelism

Parallelize independent files first.

```text
scheduler
├── VM 1 → file A
├── VM 2 → file B
└── VM 3 → file C
```

Use longest-remaining-file first among runnable files. This reduces the final long tail while keeping the rule inspectable.

Do **not** assign two live workers to the same Drive file. A single resumable Drive upload has one authoritative confirmed offset, so same-file writes remain serialized.

If one worker disappears, its stale assignment may be reclaimed after the heartbeat safety window. The replacement worker must reconcile the remote Drive offset before requesting the next Baidu range.

## Cross-VM recovery

A VM owns no durable bytes.

For a file of size `N`, the durable progress value is the byte offset that Drive has actually confirmed. Example:

```text
repo checkpoint:  12.0 GiB
Drive says:       12.5 GiB
```

The next worker resumes from **12.5 GiB**.

The repository value must never force Drive backwards. Remote reconciliation wins because a previous VM may have committed a chunk immediately before it disappeared.

The next Baidu request starts at that confirmed byte:

```http
Range: bytes=<confirmed_offset>-<bounded_end>
```

The worker discards the local chunk only after Drive has confirmed the corresponding range.

## Runner disk safety

The scheduler never plans against the runner's advertised disk size directly.

For each chunk:

```text
usable = free_disk - 4 GiB reserve
chunk  = min(512 MiB, usable, remaining file bytes)
```

If no positive chunk fits, the worker pauses instead of filling the filesystem.

The implementation should require at most a small bounded number of chunks on disk. Download/upload overlap may later use double buffering, but it must remain bounded and must not change durable semantics.

## Runtime safety

A worker stops taking new chunks at the 5-hour soft boundary. It uses the remaining workflow margin to finish/reconcile the current operation, save durable state, refresh public status, and hand control back to the scheduler.

The workflow hard timeout target is 5 hours 30 minutes. Do not intentionally run to GitHub's absolute limit.

A hard VM loss is handled by the same remote reconciliation path; it is not a separate recovery mode.

## State split

Public durable state may contain:

- task/file IDs;
- public logical paths and source metadata;
- file size/hash;
- Baidu tool-owned staging identity;
- public status/progress;
- confirmed byte offset;
- Drive object ID after it is safe to expose.

Sensitive durable state must never be plaintext in the public repository. In particular, a Google resumable-session URI is capability-bearing state and must be authenticated-encrypted before persistence. The encryption key comes from an Actions secret; the repository stores only ciphertext.

Do not build a general secret database. Encrypt only the small capability state that must survive VM replacement.

## Completion

A file is complete only after independent Drive verification succeeds. Task completion additionally requires cleanup of only the tool-owned Baidu staging objects that were durably registered for that task.

Google Drive destination objects are never cleanup targets.

## Current implementation boundary

Implemented now:

- Release-backed control plane;
- durable task/checkpoint handling;
- headless mover bridge;
- pure deterministic scheduler policy and tests.

Still to implement before live transfer:

- bounded Baidu range relay instead of full-file cache transfer;
- resumable Drive chunk writer and remote-offset query;
- per-file durable worker state/heartbeats;
- encrypted resumable-session persistence;
- scheduler-to-worker dispatch with independent-file parallelism;
- final authentication provisioning and live cross-VM acceptance tests.
