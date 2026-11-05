# One-time authorization

The bot's normal use needs **no browser sessions or refreshed cookies**. You authorize Baidu and Google once on your Windows PC; credentials are installed as GitHub Actions Secrets and refreshed by the bot. The fixed Release remains the only transfer control surface.

## 1. One-time prerequisites

- **Baidu:** a Baidu Netdisk developer application with App Key, Secret Key and its assigned `/apps/<app-name>` directory. The app must be allowed to call share verify/list/transfer and file management/download APIs. Account login itself cannot grant developer API entitlements.
- **Google:** a dedicated OAuth client with the Drive API enabled; for long-lived refresh tokens, avoid leaving the Google OAuth consent app in External/Testing status.
- **Local commands:** Python 3, [GitHub CLI](https://cli.github.com/), and [rclone](https://rclone.org/downloads/). Sign in to GitHub CLI with `gh auth login`.

Create your dedicated Google rclone remote once with `rclone config`: name `bdm-drive`, storage `drive`, scope `drive.file`, your own OAuth client ID and secret, and browser-based Google authorization. The remote must contain a refresh token.

Find the configuration with:

```powershell
rclone config file
```

## 2. Run the one-time login helper (no repo clone)

Download **only the standalone authorization script** from this repository into your local temporary directory:

```powershell
$setup = Join-Path $env:TEMP 'baidu-drive-authorize.py'
Invoke-WebRequest 'https://raw.githubusercontent.com/teddyli18000/web-ingest/main/baidu-drive/authorize_once.py' -OutFile $setup
python $setup --rclone-config "$env:APPDATA\rclone\rclone.conf"
```

The helper will:

1. Ask for the Baidu developer App Key, Secret Key and application folder once.
2. Request a **Baidu device code**, open its verification/QR page, and wait for your approval. You can confirm the login with your existing Baidu account; there is no need to paste a token.
3. Upload exactly three repository Secrets via `gh secret set`, with values on standard input rather than command arguments: `BAIDU_DRIVE_BAIDU_OAUTH`, `BAIDU_DRIVE_RCLONE_CONFIG`, and `BAIDU_DRIVE_STATE_KEY`.

For an app that does not support device-code login, rerun the helper with `--baidu-login code`; this opens the older one-time Baidu authorization-code page.

If the helper finds existing Baidu Drive Secrets, it stops before changing anything. **Do not rerun setup over an active installation**: replacing its AES key would make the persisted OAuth and Drive session state unreadable.

## 3. Initialize and test

Open [Baidu Drive Auth Keepalive](https://github.com/teddyli18000/web-ingest/actions/workflows/baidu-drive-auth-keepalive.yml) → **Run workflow** once. It initializes the master-controlled encrypted Baidu OAuth state and checks Google refresh-token functionality.

Then submit a small public Baidu share through the [fixed Release](https://github.com/teddyli18000/web-ingest/releases/tag/baidu-drive-live) to verify the app's share permissions and Drive upload. After that, test a large file that crosses a worker restart and multiple independent files.

Only the authorization and real-account acceptance are user-dependent; the master scheduler, resumable relay and refresh workflows are automatic.

## Normal operation

- The weekly credential-only keepalive checks both providers without launching transfer workers.
- The master rotates Baidu refresh tokens and stores only AES-GCM ciphertext in `state/auth/baidu-oauth.json`. File workers only consume short-lived access tokens.
- Google access tokens are refreshed automatically from the configured Google grant.
- Credentials and capability URLs never belong in public Release text, Git commits, or Actions logs.
- Provider revocation, authorization-scope changes or lack of Baidu share-API entitlement require direct account action; ordinary token expiry does not.

**Baidu share API entitlement:** if the app is not authorized to use the relevant share endpoints, the integration blocks at the provider permission check. The solution is obtaining that entitlement from Baidu; repeatedly scanning a QR code cannot grant it.
