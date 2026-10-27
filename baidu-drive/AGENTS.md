# AGENTS.md — baidu-drive

This task moves public Baidu Netdisk shares to Google Drive through a Release-backed Actions control plane. Keep implementation task-local, small, recoverable, and fail-closed around authentication, remote mutation, and cleanup.

Read `README.md` and `SCHEDULER.md` before changing scheduling, worker state, transfer buffering, or recovery behavior.

## First principles

- GitHub-hosted VMs are disposable. No important byte or credential may exist only on one runner.
- Baidu tool-owned staging is the durable readable source.
- Google Drive resumable/verified remote state is the durable writable destination truth.
- Repository state is a recovery hint and public status projection; it must never force a proven remote state backwards.
- Keep one normal data path: exact Baidu Range response body -> direct Drive resumable PUT. Small files are one final chunk; large files are many fixed-size non-final chunks.
- A relay chunk is a network byte window, not a disk-backed file. Do not reintroduce chunk files or Release assets without a measured, concrete failure mode.

## Control plane

Fixed Release `baidu-drive-live` is the human control/status surface, not a secret store or the only durable state.

Human-editable request fields:

```text
command: none | start | retry | cancel
share_url: <public HTTPS Baidu share URL or ->
extraction_code: <public share extraction code or ->
```

Every non-`none` command is consumed back to `none`, including rejected commands. Bot-authored Release edits must not recursively run the writer.

A worker may be dispatched only after Reconcile proves the request was accepted:

- accepted `start` changes the active task ID;
- accepted `retry` increments that task's attempt;
- rejected requests must not dispatch work against an older task.

## Scheduler

`scheduler.py` is the deterministic policy layer. Keep it pure: no GitHub, Baidu, or Google calls.

Initial policy:

```text
max active file workers = 3
chunk target            = 512 MiB
soft runtime stop       = 5 h
hard workflow target    = 5 h 30 m
stale heartbeat window  = 60 m
```

The non-final chunk size must remain a positive multiple of Google Drive's 256 KiB resumable-upload quantum. Final chunks may be smaller.

Scheduling rules:

- parallelize independent files first;
- prefer longest remaining file among runnable candidates to reduce the final tail;
- never assign two live workers to the same Drive file;
- a stale worker may be reclaimed only through the documented heartbeat/reconciliation path;
- replacement workers query Drive before deciding the next Baidu byte range;
- Drive-confirmed offset wins over the repo checkpoint, even when it proves less than a stale optimistic repo hint;
- stop starting new chunks at the soft runtime boundary and leave margin for reconciliation/state persistence.

Do not add speculative heuristics or adaptive machinery without measured evidence that the simple policy is insufficient.

## State

Current task-level public state lives under `baidu-drive/state/`:

- `runtime.json` — active/last task identity;
- `tasks/<task-id>.json` — public source and non-secret status/progress;
- `checkpoints/<task-id>.sqlite.zlib.b64` — current mover checkpoint for the public transfer.

The relay scheduler may add per-file public state. Prefer one file-scoped record per independently writable file so parallel workers do not contend on a single large state object.

Public state may contain public-share manifest data, size/hash, tool-owned staging identity, status, confirmed offset, heartbeat metadata, and safe Drive IDs.

Sensitive capability state must never be plaintext in the public repository. Google resumable-session URIs are capability-bearing and must be authenticated-encrypted before persistence. Keep this mechanism narrow; do not invent a general secret database.

Do not create timestamp-only commits. State writes should correspond to semantic changes.

## Transfer and recovery

The normal transfer contract is:

```text
Baidu staged file
  -> exact bounded HTTP Range
  -> direct response-body stream
  -> Drive resumable PUT for the same byte window
  -> query/confirm remote offset
  -> repeat
  -> independent final Drive verification
  -> tool-owned staging cleanup
```

Do not buffer a whole relay chunk in RAM or on disk. HTTP transport buffers must remain bounded and independent of the configured 512 MiB byte window.

A runner's local files, TCP connection, or filesystem are never required for recovery. If an upload request is interrupted, query Drive first, then request only the unconfirmed remainder from Baidu.

The current standalone mover bridge still uses a full-file local-cache pipeline while the direct relay executor is being implemented. Do not mistake that compatibility bridge for the final Actions data path.

Google Drive destination objects are never cleanup targets. Cleanup may remove only durably registered tool-owned local/Baidu staging after destination verification.

## Mover bridge

`baidu-drive/mover/` is an Actions adapter around the standalone mover; it is not a second independent transfer implementation.

The integration currently pins:

```text
teddyli18000/baidu-drive-mover
a9e76feb18fe9ca1ac680d0ea555aac684d622de
```

That revision includes exact bounded Baidu byte-range reads and passed the standalone mover CI before being pinned here.

`repository-integrity.yml` copies:

- `mover/action-main.go` -> pinned module `cmd/baidu-drive-action/main.go`;
- `mover/action_recovery.go` -> pinned module `internal/state/action_recovery.go`.

Then it runs relevant mover tests and builds the bridge on Linux. Do not change the pin or bridge contract without updating task documentation and passing this gate.

The bridge must not launch interactive browsers.

## Workflows and concurrency

- `baidu-drive-reconcile.yml` owns Release control and accepted-request dispatch.
- `baidu-drive-worker.yml` is the current fail-closed serialized compatibility worker while the file relay is built.
- Control-plane writes remain serialized.
- Data-plane file workers will use independent file ownership; do not serialize all data transfer behind the control-plane concurrency group once file-scoped state is live.
- Same-file writes must still be serialized.
- Normal state commits must not recursively trigger the Release control path.

Until authentication provisioning and relay execution are explicitly configured, the live worker must remain at `BLOCKED_AUTH_SETUP`; do not fake success or introduce credentials merely to make a smoke test pass.

## Authentication and public-repository safety

Only public Baidu share URLs may be submitted. Everything committed here, in Release bodies, Actions logs, summaries, artifacts, and Git history must be treated as public.

Never commit or expose:

- account passwords, API keys, or tokens;
- Baidu cookies/session data;
- OAuth access or refresh tokens;
- rclone credential configuration;
- private headers;
- signed/expiring credential-bearing URLs;
- plaintext Drive resumable-session URIs;
- private-source data;
- secret-derived diagnostics.

Authentication files are runner-local and ephemeral. The current compatibility worker recognizes these path interfaces:

```text
BAIDU_DRIVE_BAIDU_AUTH_FILE
BAIDU_DRIVE_RCLONE_CONFIG_FILE
BAIDU_DRIVE_RCLONE_BIN
BAIDU_DRIVE_BRIDGE_BIN
```

They are interfaces, not the final credential-provisioning decision.

## Validation

After changes, run at minimum:

```bash
python3 -m py_compile baidu-drive/*.py
python3 -m unittest discover -s baidu-drive/tests -v
python3 tools/check-repository-integrity.py
```

Mover bridge or pin changes additionally require the Go integration build/tests in `repository-integrity.yml` to pass.
