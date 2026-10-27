# AGENTS.md — baidu-drive

This task moves public Baidu Netdisk shares to Google Drive through a Release-backed Actions control plane. Keep implementation task-local and fail closed around authentication, recovery, remote mutation, and cleanup.

## Boundaries

- Fixed Release `baidu-drive-live` is the human control/status surface, not a secret store or the only durable state.
- Only public Baidu share URLs may be submitted. The repository, Release, task JSON, and mover checkpoints are public.
- Authentication material must come only from GitHub Actions secrets or another explicitly approved secret source. Never commit it, echo it, put it in Step Summary, or upload it as an artifact.
- Authentication files are runner-local and ephemeral. Durable state must never contain account cookies, OAuth tokens, rclone credential configuration, private headers, signed credential-bearing URLs, or private-source data.
- Transfer implementation belongs under `baidu-drive/`; workflows stay thin.
- Google Drive destination objects are never cleanup targets. Cleanup may remove only durably registered tool-owned local/Baidu staging after destination verification.
- Preserve resumability and idempotency. A job restart must reconcile durable state rather than blindly replay remote mutations.

## Release protocol

Human-editable request fields:

```text
command: none | start | retry | cancel
share_url: <public HTTPS Baidu share URL or ->
extraction_code: <public share extraction code or ->
```

Every non-`none` command is consumed back to `none`, including rejected commands. Bot-authored Release edits must not recursively run the writer.

A worker may be dispatched only after Reconcile proves the request was accepted:

- accepted `start` changes the active task ID;
- accepted `retry` increments that same task's `attempt`;
- rejected requests must not dispatch work against an older task.

## State

Durable public state lives only under `baidu-drive/state/`:

- `runtime.json` — active/last task identity;
- `tasks/<task-id>.json` — public source and non-secret progress/status;
- `checkpoints/<task-id>.sqlite.zlib.b64` — compressed mover SQLite checkpoint for that public transfer.

Do not create timestamp-only commits. State writes should correspond to semantic changes.

The checkpoint may retain public-share manifest metadata and mover state, but never authentication material. Runner-local downloaded bytes are not durable state and must not be committed.

On a new runner, cache-dependent pre-verification file states are rewound to `BAIDU_STAGED` by the bridge recovery shim. Known Drive IDs are retained so normal mover reconciliation can safely adopt a remote commit after re-downloading source bytes.

## Mover bridge

`baidu-drive/mover/` is a small Actions adapter around the standalone mover; it is not a second independent transfer implementation.

The integration currently pins:

```text
teddyli18000/baidu-drive-mover
f4ca661d367aa2a067344efa989f0bfc95b64618
```

`repository-integrity.yml` copies:

- `mover/action-main.go` -> pinned module `cmd/baidu-drive-action/main.go`;
- `mover/action_recovery.go` -> pinned module `internal/state/action_recovery.go`.

Then it runs relevant mover tests and builds the bridge on Linux. Do not change the pin or bridge contract without updating task documentation and passing this gate.

The bridge must not launch interactive browsers. Authentication must already be prepared by the workflow in ephemeral files before the bridge starts.

## Workflows and concurrency

- `baidu-drive-reconcile.yml` owns Release control and worker dispatch.
- `baidu-drive-worker.yml` owns transfer/checkpoint execution.
- All writers use concurrency group `baidu-drive-live-state` with `cancel-in-progress: false`.
- Normal task/checkpoint commits must not recursively trigger the control plane.
- Until authentication provisioning is explicitly configured, the worker must remain at `BLOCKED_AUTH_SETUP`; do not fake success or silently introduce credentials to make a smoke test pass.

## Authentication interface

The worker currently recognizes only paths to runner-local prepared files:

```text
BAIDU_DRIVE_BAIDU_AUTH_FILE
BAIDU_DRIVE_RCLONE_CONFIG_FILE
BAIDU_DRIVE_RCLONE_BIN
BAIDU_DRIVE_BRIDGE_BIN
```

These are an internal boundary, not a decision about how secrets are provisioned. Keep the producer replaceable so later OAuth/Secret decisions do not require redesigning the transfer state machine.

## Validation

After changes, run at minimum:

```bash
python3 -m py_compile baidu-drive/controller.py baidu-drive/worker.py
python3 -m unittest discover -s baidu-drive/tests -v
python3 tools/check-repository-integrity.py
```

Mover bridge or pin changes additionally require the integration build/tests in `repository-integrity.yml` to pass.
