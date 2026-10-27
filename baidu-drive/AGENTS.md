# AGENTS.md — baidu-drive

This task moves public Baidu Netdisk shares to Google Drive through a Release-backed Actions control plane. Keep it task-local, small, recoverable, and fail-closed around authentication, remote mutation, reconciliation, and cleanup.

Read `README.md` and `SCHEDULER.md` before changing scheduling, worker state, transfer buffering, or recovery behavior.

## First principles

- GitHub-hosted VMs are disposable. No important payload byte or credential may exist only on one runner.
- Tool-owned Baidu staging is the durable readable source.
- Google Drive verified/resumable remote state is the durable writable truth.
- Repository state is a checkpoint and public coordination record; it must not override contradictory proven remote state.
- There is exactly one global scheduler: `baidu-drive-worker.yml` / `prepare_worker.py`.
- Keep one normal non-empty-file data path: exact Baidu Range response body -> direct Drive resumable PUT.
- A 512 MiB relay window is a byte interval, not a disk-backed chunk or RAM-sized buffer.
- Do not reintroduce Release asset staging, whole-file Actions cache, a second scheduler, or same-file multi-VM writes without a concrete measured failure mode.

## Control plane

Fixed Release `baidu-drive-live` is the human control/status surface, not a secret store or database.

Human-editable fields:

```text
command: none | start | retry | cancel
share_url: <public HTTPS Baidu share URL or ->
extraction_code: <public share extraction code or ->
```

Every non-`none` command is consumed back to `none`, including rejected commands. Bot-authored Release edits must not recursively run the writer.

Reconcile may dispatch the master only after proving a `start` or `retry` request was accepted. Rejected requests must never dispatch work against an older task.

## Master scheduler

`scheduler.py` is the pure deterministic selection policy. `prepare_worker.py` owns orchestration and is the only component allowed to make global work decisions.

Initial policy:

```text
max active file workers = 3
relay window            = 512 MiB
soft runtime stop       = 5 h
hard workflow timeout   = 5 h 30 m
stale lease window      = 60 m
```

Rules:

- parallelize independent files first;
- prefer longest remaining file among runnable candidates;
- never assign two live workers to the same Drive file;
- same-file workflow concurrency is additionally keyed by task + file;
- replacement workers query Drive before choosing the next Baidu byte range;
- Drive-confirmed offset wins over stale repo checkpoint state;
- workers stop starting new windows at the soft runtime boundary;
- file-worker completion wakes the same master through `workflow_run: completed`; do not add a polling watchdog merely for ordinary VM failure.

Do not add speculative adaptive scheduling without measured evidence.

## State

Task-level public state:

- `state/runtime.json` — active/last task;
- `state/tasks/<task-id>.json` — task status/progress;
- `state/checkpoints/<task-id>.sqlite.zlib.b64` — mover checkpoint.

File-level public state:

- `state/files/<task-id>/<file-id>.json` — immutable source identity plus lease, offset/hash, encrypted session, and verified Drive result.

Prefer file-scoped writes so independent workers do not contend on one large state object. Do not create timestamp-only commits.

A Drive resumable-session URI is capability-bearing state. It must remain AES-256-GCM sealed with AAD bound to task + file. The master key is future Actions-secret material; never commit it.

## Transfer and recovery

Normal non-empty-file contract:

```text
Baidu staged file
  -> exact bounded HTTP Range
  -> direct response-body stream
  -> Drive resumable PUT
  -> Drive status reconciliation
  -> aligned streamed-MD5 checkpoint
  -> repeat
  -> independent final Drive ID + size + MD5 proof
```

Do not buffer the whole relay window in RAM or on disk.

If a PUT is interrupted, never infer progress from local byte counts. Ask Drive. If Drive is behind a repo hint, rebuild the hash prefix from Baidu to the proven remote offset before continuing.

Zero-byte files use only the small Drive create/adopt branch because there are no bytes to range-read. Same-name destination conflicts must fail closed.

If a resumable session expires:

- query exact Drive parent + filename before any replacement;
- unique expected size + source-verified MD5 may be adopted;
- proven absence permits clearing only session-scoped progress and starting from zero;
- duplicate/conflicting objects become `BLOCKED_RECONCILE`;
- network/auth failure during reconciliation must not be treated as absence.

## Prepare/staging/cleanup

The master serializes the mover SQLite checkpoint. Its prepare bridge may scan/resume, import verified file results, perform guarded cleanup, ensure the Drive directory tree, stage one bounded batch, and export a relay manifest.

The standalone mover's local-cache transfer path remains for its Windows CLI/legacy compatibility. Do not route the Actions relay through that cache pipeline.

Google Drive destination objects are never cleanup targets. Cleanup may remove only durably registered tool-owned Baidu staging after Drive verification has been imported into SQLite.

## Mover integration

Actions adapters are compiled against:

```text
teddyli18000/baidu-drive-mover
a9e76feb18fe9ca1ac680d0ea555aac684d622de
```

That pinned revision supplies the hardened scanner/stager/state/Drive-tree/cleanup code and exact bounded Baidu byte-range reads.

Task-local files under `baidu-drive/mover/` are Actions adapters, not a forked second product. `repository-integrity.yml` copies them into the pinned module, runs the relevant Go tests, and compiles the action/prepare/relay binaries on Linux.

Do not change the pin or adapter contract without passing that integration gate and updating docs.

Interactive browsers are forbidden in Actions workers.

## Workflows and concurrency

- `baidu-drive-reconcile.yml` — Release request validation/consumption and accepted start/retry dispatch.
- `baidu-drive-worker.yml` — **single master scheduler**, serialized by `baidu-drive-live-state`; also triggered by file-worker completion.
- `baidu-drive-file-worker.yml` — one leased file per disposable VM; different files may run concurrently.

Do not serialize all file payload transfer behind `baidu-drive-live-state`. Do not let file workers write task-global SQLite state.

Until final authentication provisioning exists, live execution must remain fail-closed at `BLOCKED_AUTH_SETUP`; never add credentials merely to make a smoke test green.

## Authentication and public-repository safety

Only public Baidu share URLs belong here. Treat Git history, Releases, Actions logs, summaries, and artifacts as public.

Never commit or expose:

- passwords, API keys, access/refresh tokens;
- Baidu cookies/session data;
- rclone credential configuration;
- private headers;
- signed/expiring credential-bearing URLs;
- plaintext Drive resumable-session URIs;
- the AES state key;
- private-source data;
- secret-derived diagnostic dumps.

Future prepare runner-local interfaces:

```text
BAIDU_DRIVE_BAIDU_AUTH_FILE
BAIDU_DRIVE_RCLONE_CONFIG_FILE
BAIDU_DRIVE_RCLONE_BIN
```

Future file-relay runner-local interfaces:

```text
BAIDU_DRIVE_BAIDU_AUTH_FILE
BAIDU_DRIVE_GOOGLE_ACCESS_TOKEN_FILE
BAIDU_DRIVE_STATE_KEY_FILE
```

They are interfaces, not the final credential-provisioning decision.

## Validation

After changes, run at minimum:

```bash
python3 -m py_compile baidu-drive/*.py
python3 -m unittest discover -s baidu-drive/tests -v
python3 tools/check-repository-integrity.py
```

Changes under `mover/`, workflow build wiring, or the mover pin additionally require the Go integration tests/builds in `repository-integrity.yml` to pass.
