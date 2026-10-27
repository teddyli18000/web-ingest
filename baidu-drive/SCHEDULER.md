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

Every file uses the same direct relay:

```text
Baidu staged file
    ↓ exact HTTP byte range
response body stream
    ↓ exact Drive resumable PUT
Google Drive
```

The scheduled 512 MiB chunk is a **network byte window**, not a file written to runner disk. A small file naturally completes in one final chunk. A large file uses many fixed-size non-final chunks. No complete source file or relay chunk has to fit on runner disk.

Google Drive requires non-final resumable chunks to be aligned to 256 KiB. The initial 512 MiB chunk size is a fixed compatible multiple. Do not make chunk size depend on runner disk capacity.

Release assets are not part of the normal data path. Baidu already provides the durable source copy, so uploading chunks to GitHub and downloading them again would add another transfer, another lifecycle, and another failure surface without adding required durability.

## Scheduler ownership

There is one logical scheduler. It is the only component allowed to decide what work should run next.

Workers do not choose files, split ownership, or infer global concurrency. A worker receives one file assignment and advances that file until it completes, reaches the soft runtime boundary, or hits a retryable block.

The scheduler policy is deterministic and lives in `scheduler.py`.

Initial policy:

- maximum active file workers: **3**;
- relay chunk target: **512 MiB**;
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

That Baidu response body is streamed directly as the Drive request body. When Drive confirms the request, the scheduler may advance the durable confirmed offset. If the connection or VM dies first, the replacement asks Drive what it actually retained and re-requests only the remaining Baidu bytes.

## Runner resource safety

The normal relay does not materialize a 512 MiB chunk on disk. Memory usage must also stay bounded by the HTTP transport buffers rather than by chunk size.

Runner disk remains available for tiny state/configuration/runtime files only. File size therefore does not determine whether a GitHub-hosted runner can execute the transfer.

Do not add disk-backed chunk buffering or double-buffer files merely for throughput. If measurements later prove direct streaming insufficient, document the concrete bottleneck before introducing another buffering layer.

## Runtime safety

A worker stops starting new chunks at the 5-hour soft boundary. It uses the remaining workflow margin to reconcile any in-flight Drive request, save durable state, refresh public status, and hand control back to the scheduler.

The workflow hard timeout target is 5 hours 30 minutes. Do not intentionally run to GitHub's absolute limit.

A hard VM loss is handled by the same Drive-offset reconciliation path; it is not a separate recovery mode.

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
- pure deterministic scheduler policy and tests;
- a Baidu API primitive for exact bounded byte ranges.

Still to implement before live transfer:

- direct Baidu-range-to-Drive-resumable relay executor;
- Drive resumable-session creation and remote-offset query;
- per-file durable worker state/heartbeats;
- encrypted resumable-session persistence;
- scheduler-to-worker dispatch with independent-file parallelism;
- final authentication provisioning and live cross-VM acceptance tests.
