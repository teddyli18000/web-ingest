# Quark → Google Drive

Independent provider task connected to the shared [one-master / three-worker pool](../tools/cloud-drive/README.md).
Development entry: [Issue #24](https://github.com/teddyli18000/web-ingest/issues/24).

## Source protocol

Reference: [gopeed-extension-quark](https://github.com/iGwkang/gopeed-extension-quark) (MIT).
`api.py` implements Quark share-token exchange, recursive directory scan, tool-owned folder staging, save-task polling, Quark signed-link issuance, and `__puus` rotation. The separate browser helper `authorize_once.py` obtains personal cookies using a dedicated local Chrome profile and submits only GitHub Actions Secrets over the GitHub CLI.

## Isolation and transfer rules

- Quark task state: `quark-drive/state/` only; separate fixed `quark-drive-live` Release.
- Quark secrets: `QUARK_DRIVE_QUARK_SESSION`, `QUARK_DRIVE_RCLONE_CONFIG`, `QUARK_DRIVE_STATE_KEY`.
- Google Drive resumable upload, streaming MD5 verification, source file lease and checkpoints are implemented in `mover/`, separate from Baidu's production source.
- The shared master owns *three total workers*. Each Quark worker reads a single source fid and refreshes its signed link as necessary.
- A staged Quark file is deleted only after independent Google Drive size and MD5 verification. Interrupted requests do not erase staged source objects.
- Transient provider faults retry with checkpointed exponential backoff/jitter; authentication and ambiguous target objects require resolution rather than speculative replay.

## Local authorization

The helper will be used after the isolated Quark workflows and CI are deployed:

```powershell
$setup = Join-Path $env:TEMP 'quark-drive-authorize.py'
Invoke-WebRequest 'https://raw.githubusercontent.com/teddyli18000/web-ingest/main/quark-drive/authorize_once.py' -OutFile $setup
python $setup
```

Uses your already configured local `bdm-drive` rclone remote and GitHub CLI login. No Quark password, Cookie, or Google OAuth refresh token belongs in a public Release, log, Issue, or chat.
