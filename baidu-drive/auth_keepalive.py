"""Monthly keepalive for independently rotating OAuth credentials."""
from __future__ import annotations

import os
from pathlib import Path

import auth_provision
import controller
import oauth_state


def maintain(repo, oauth_secret: str, google_config: str, state_key: str, temp: Path) -> bool:
    if not (oauth_secret and google_config and state_key):
        return False
    oauth_state.ensure_fresh(repo, oauth_secret, state_key)
    temp.mkdir(mode=0o700, parents=True, exist_ok=True)
    config = temp / "google-rclone.conf"
    token = temp / "google-access"
    expiry = temp / "google-expiry"
    auth_provision.write_private(config, google_config)
    auth_provision.refresh_google_token(config, token, expiry)
    return True


def main() -> int:
    repo = controller.GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    configured = maintain(
        repo,
        os.environ.get("BAIDU_DRIVE_BAIDU_OAUTH", ""),
        os.environ.get("BAIDU_DRIVE_RCLONE_CONFIG", ""),
        os.environ.get("BAIDU_DRIVE_STATE_KEY", ""),
        Path(os.environ["RUNNER_TEMP"]) / "baidu-drive-keepalive",
    )
    print("Baidu Drive OAuth keepalive completed." if configured
          else "Baidu Drive OAuth keepalive not configured; no credentials touched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
