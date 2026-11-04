# One-time authorization

The long-running bot never asks for browser cookies. The authorization tool runs **locally once** on your own Windows computer; it sends bootstrap credentials directly into three GitHub Actions Secrets using the authenticated GitHub CLI. It never sends tokens through the public Release, commits plaintext credentials, or stores the short-lived authorization code in Git.

## Before running the helper

1. Create or use your **own Baidu Netdisk developer application**. Record its App Key, Secret Key, and actual application path `/apps/<application-name>`. The app must be permitted to call the OAuth share verify/list/transfer endpoints and file management/metadata APIs. The published personal-developer sharing API access policy has historically been restrictive; an OAuth login alone does **not** grant APIs that the app is not approved to use.
2. Create your **own Google OAuth client** with Google Drive enabled, and set the OAuth consent app to a suitable **In production** publishing status. Google External/Testing credentials can have seven-day refresh-token expiry. Authorize an rclone remote named exactly `bdm-drive`, type `drive`, with scope `drive.file`, its own `client_id` and `client_secret`, and a token JSON containing a refresh token.
3. Have Python 3 and GitHub CLI `gh` installed locally. Run `gh auth login` once if not already authenticated. Run `rclone config file` to find the config containing your `bdm-drive` remote.

## Run on your own machine

From a local checkout of `web-ingest`:

```powershell
python baidu-drive/authorize_once.py --rclone-config "$env:APPDATA\rclone\rclone.conf"
```

The helper asks for the Baidu App Key/Secret, application directory, opens Baidu's OAuth authorization page, and asks for the one-time authorization code. It then writes these repository Actions Secrets using `gh secret set` via standard input:

- `BAIDU_DRIVE_BAIDU_OAUTH`: encrypted by GitHub Secrets, contains client ID, client secret, the **initial** Baidu refresh token, and app directory;
- `BAIDU_DRIVE_RCLONE_CONFIG`: only the `[bdm-drive]` Google remote configuration;
- `BAIDU_DRIVE_STATE_KEY`: a randomly generated 32-byte key, Base64-encoded.

The helper never prints the authorization token, refresh tokens, or Secret values.

Then dispatch [Baidu Drive Auth Keepalive](https://github.com/teddyli18000/web-ingest/actions/workflows/baidu-drive-auth-keepalive.yml) once to bootstrap the bot's encrypted OAuth state. Subsequent Baidu refreshes use the **latest** encrypted refresh token, not the initial one stored in the Secret. Only the serialized master rotates it. The monthly keepalive independently checks both providers even when no transfer is running.

Finally, use the fixed [Baidu → Google Drive Release](https://github.com/teddyli18000/web-ingest/releases/tag/baidu-drive-live) to start a transfer. The public Release carries only public share information and commands. The bot scans, stages, streams, resumes, verifies, cleans up, and reports progress.

## Authorization acceptance

Before calling the system fully live, test against a small public share containing a directory and a nonempty file. Confirm through the Release that the share/list/transfer endpoints were authorized for **your application**, Google Drive sees the matching ID/size/MD5, and tool-owned staging was cleaned. Then test a large file that spans a worker restart, and a task with independent files that can occupy multiple workers.

A response like `errno=-6` or an app-scope/permission error means the Baidu app is **not authorized for that API**. The bot must stop; it cannot elevate OAuth permissions, request a CAPTCHA on your behalf, or replace missing app capabilities with browser cookies. Fix the developer-app entitlement rather than reinstalling credentials or retrying blindly.

## Stable state ownership

- `state/auth/baidu-oauth.json` contains only AES-GCM ciphertext, never plaintext tokens.
- OAuth refresh-token rotation is serialized under the master/keepalive workflow concurrency group.
- Access tokens, the AES key, rclone configuration, and Google refresh token exist only as GitHub Actions Secrets or ephemeral runner-local files.
- Never replace the state key while resumable file sessions or the encrypted Baidu refresh token still exist. Re-running the initial authorization helper on an existing installation is a rebootstrap, not a routine renewal.

Normal renewal is automatic. Reauthorization is needed only if the provider revokes the authorization, changes its API permissions, or invalidates the long-lived refresh grant.
