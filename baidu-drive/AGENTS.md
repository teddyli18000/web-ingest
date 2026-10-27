# AGENTS.md — baidu-drive

This task is a public-source transfer control plane. Keep the implementation task-local and fail closed around authentication or destructive cleanup.

## Boundaries

- The fixed GitHub Release is the human control/status surface, not a secret store or the only durable state.
- Machine state belongs only under `baidu-drive/state/` and must remain free of account credentials, OAuth tokens, cookies, signed URLs, private headers, or private source data.
- Only public Baidu share URLs may be submitted through the Release. The repository and Release are public.
- Authentication material must eventually come from GitHub Actions secrets or another explicitly approved secret store. Never commit it, echo it, put it in Step Summary, or upload it as an artifact.
- Transfer implementation belongs under `baidu-drive/`; workflows stay thin.
- Google Drive destination objects are never cleanup targets. Future cleanup may remove only tool-owned temporary local/Baidu staging after destination verification.
- Preserve resumability and idempotency. A job restart must reconcile durable state rather than blindly replay remote mutations.

## Release protocol

Fixed tag: `baidu-drive-live`.

Human-editable request fields:

```text
command: none | start | retry | cancel
share_url: <public HTTPS Baidu share URL or ->
extraction_code: <public share extraction code or ->
```

The Action consumes every non-`none` command back to `none`, including rejected commands, so later reconciles do not replay stale requests. Bot-authored Release edits must not recursively run the writer.

## State

- `state/runtime.json` tracks active/last task identity.
- `state/tasks/<task-id>.json` stores durable non-secret task state.
- Do not create timestamp-only commits. State writes should correspond to semantic changes.
- All writers use the shared `baidu-drive-live-state` concurrency group with `cancel-in-progress: false`.

## Current phase

The Release control plane is implemented first. Until OAuth/secrets and the transfer worker are explicitly configured, `start` and `retry` stop at `BLOCKED_AUTH_SETUP`. Do not fake a successful transfer or silently add credential material to make a smoke test pass.

## Validation

After changes, run at minimum:

```bash
python3 -m py_compile baidu-drive/controller.py
python3 -m unittest discover -s baidu-drive/tests -v
python3 tools/check-repository-integrity.py
```
