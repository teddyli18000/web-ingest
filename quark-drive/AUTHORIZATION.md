# Quark Drive authorization

First-time sign-in is local only. The helper opens a **separate Chrome profile** for Quark. Your existing Baidu account and Google Drive destination are unchanged.

## Windows PowerShell

Prerequisites: GitHub CLI (`gh auth status`), Python 3, Chrome, rclone `bdm-drive` (already configured for the Baidu mover).

```powershell
python -m pip install playwright
$setup = Join-Path $env:TEMP 'quark-drive-authorize.py'
Invoke-WebRequest 'https://raw.githubusercontent.com/teddyli18000/web-ingest/main/quark-drive/authorize_once.py' -OutFile $setup
python $setup
```

Sign in to Quark Netdisk in the dedicated Chrome window. The helper verifies account access, writes three **separate GitHub Actions Secrets** and wakes the common Master:

- `QUARK_DRIVE_QUARK_SESSION` — browser Cookie
- `QUARK_DRIVE_RCLONE_CONFIG` — existing Google `bdm-drive` OAuth config, separately scoped
- `QUARK_DRIVE_STATE_KEY` — private 256-bit encrypted-checkpoint key

Secrets are submitted to GitHub through `gh secret set` standard input, not in shell arguments, Release body, Issue or commits. Server-rotated `__puus` is stored in an encrypted state record and reused until a fresh local login.

## Transfer control

Edit the body of [the fixed Quark Release](https://github.com/teddyli18000/web-ingest/releases/tag/quark-drive-live):

```text
command: start
share_url: https://pan.quark.cn/s/YOUR_PUBLIC_SHARE_ID
extraction_code: -
```

Set `extraction_code` to the public share's extraction code when needed. After accepting a task, the bot resets `command` to `none`; progress, errors and destination link appear on the same Release. `retry` resumes the same task, and `cancel` cancels it.

Only if Quark or Google authentication expires will the bot publish a fixed `[Quark Drive] Login required` Issue. Re-run the local helper, without altering the running task. It preserves the existing upload session and verified Drive offsets.

## Login-only refresh

If you later need to renew the Quark login, run the same script. The existing Google OAuth secret and encryption key remain intact. `--google-only` renews only Google's saved OAuth config.
