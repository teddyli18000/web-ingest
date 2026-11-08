# One-time login and automatic recovery

Use the same normal Baidu Netdisk account you already use in Chrome or LinkSwift. **No Baidu developer application, App Key, or Secret Key is required.** The fixed [Release](https://github.com/teddyli18000/web-ingest/releases/tag/baidu-drive-live) remains the transfer controller.

## Your first setup (Windows, no repository clone)

Install Python 3, [GitHub CLI](https://cli.github.com/) and [rclone](https://rclone.org/downloads/) if missing. Sign in to GitHub with:

```powershell
gh auth login
python -m pip install playwright
```

### Google Drive (one-time personal OAuth app)

Use **your own** Google Cloud OAuth Desktop client in a project with **Google Drive API enabled** and OAuth Audience set to **In production**. The built-in shared rclone OAuth client is being retired in 2026; do not use it for unattended transfers.

Configure the existing `bdm-drive` remote on your local Windows machine:

1. Open the downloaded OAuth Desktop client JSON; use its `installed.client_id` and `installed.client_secret` values. Keep the JSON and both credentials private.
2. Run `rclone config`, choose **Edit existing remote** (`e`) and select `bdm-drive`.
3. Set its `client_id` and `client_secret` to the newly created Google OAuth values. Keep the backend `drive` and scope exactly `drive.file`. Leave unrelated values at their defaults.
4. Save, then reauthorize with the new client:

```powershell
rclone config reconnect bdm-drive:
rclone lsd bdm-drive:
```

When asked to refresh the existing token, select **Yes**, and finish the browser-based Google login. Listing an empty Drive root can be normal with the `drive.file` scope.

Now refresh **only the Google GitHub Secret** (no Baidu login required):

```powershell
$setup = Join-Path $env:TEMP 'baidu-drive-authorize.py'
Invoke-WebRequest 'https://raw.githubusercontent.com/teddyli18000/web-ingest/main/baidu-drive/authorize_once.py' -OutFile $setup
& "E:\\Python_Projects\\Anaconda\\python.exe" $setup --google-only
```

This replaces `BAIDU_DRIVE_RCLONE_CONFIG`, leaves the existing Baidu session and state encryption key untouched, and dispatches the master workflow. No client ID, client secret or token should be pasted into GitHub issues, releases, commits, or chat.

### Baidu (one browser window)

Download **just the local login script** and run it:

```powershell
$setup = Join-Path $env:TEMP 'baidu-drive-authorize.py'
Invoke-WebRequest 'https://raw.githubusercontent.com/teddyli18000/web-ingest/main/baidu-drive/authorize_once.py' -OutFile $setup
python $setup
```

The helper opens a **dedicated Chrome profile** (saved at `%LOCALAPPDATA%\web-ingest\baidu-drive-browser`) and visits Baidu Netdisk. Sign in in the window that appears. It waits until the actual Baidu login status is valid, then sends a browser-session snapshot to the GitHub Actions Secret `BAIDU_DRIVE_BAIDU_SESSION` **through gh CLI standard input**, never through a Release, Issue, commit or CLI argument.

On the first run it also securely initializes `BAIDU_DRIVE_STATE_KEY` and, if absent, `BAIDU_DRIVE_RCLONE_CONFIG` from your local rclone remote. On subsequent runs it **preserves the encryption key and Google authorization**. The helper dispatches `baidu-drive-worker.yml` with `reason=auth-updated`; any paused transfer automatically resumes at its existing checkpoint.

## After setup

- Normal activity requires **no browser**, no computer kept running, and no repeat login.
- The scheduler uses the latest AES-GCM-encrypted browser session state. Updated cookies from master API operations are saved to this encrypted state, so newer sessions take priority over the original GitHub Secret.
- The weekly credential-maintenance job keeps the Google OAuth grant active and maintains the encrypted Baidu session. It cannot manufacture new Baidu login cookies if Baidu revokes a session.
- If Baidu really invalidates the session, the bot sets `NEEDS_LOGIN` in the fixed Release, retains all checkpoints, and opens/reopens **one fixed GitHub Issue**, mentioning the repository owner. Re-run the **same two-line PowerShell download/run commands**. Your dedicated Chrome profile usually already has the account session and can reuse it.
- Google token refreshes are handled by rclone on each disposable runner. File workers never attempt interactive login.

No password, Chrome profile, plaintext Cookie, OAuth token, or Google Drive resumable-session URL is published in GitHub Issues, Releases or git history. Never paste credentials into any public text.

## Acceptance

After the first login, submit one small public Baidu share in the fixed Release to check real provider permissions and Drive upload. Then test independent files and a large file crossing worker replacement. The code/CI simulation does not substitute for this real-account validation.
