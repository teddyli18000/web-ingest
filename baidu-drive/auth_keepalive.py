"""Weekly encrypted browser-session maintenance and Google OAuth refresh check."""
from __future__ import annotations

import os
from pathlib import Path

import auth_provision
import auth_session
import controller


def maintain(repo, baidu_session: str, google_config: str, state_key: str, temp: Path) -> bool:
    if not (baidu_session and google_config and state_key):
        return False
    current = auth_session.read(repo, baidu_session, state_key)
    auth_session.save_if_changed(repo, baidu_session, state_key, current)
    auth_provision.validate_google(google_config, state_key)
    temp.mkdir(mode=0o700, parents=True, exist_ok=True)
    config = temp / "google-rclone.conf"
    token = temp / "google-access"
    expiry = temp / "google-expiry"
    binary = temp / "rclone"
    auth_provision.write_private(config, google_config)
    auth_provision.install_rclone(binary)
    auth_provision.refresh_google_token(config, token, expiry, binary)
    return True


def main() -> int:
    repo = controller.GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    configured = maintain(
        repo,
        os.environ.get("BAIDU_DRIVE_BAIDU_SESSION", ""),
        os.environ.get("BAIDU_DRIVE_RCLONE_CONFIG", ""),
        os.environ.get("BAIDU_DRIVE_STATE_KEY", ""),
        Path(os.environ["RUNNER_TEMP"]) / "baidu-drive-keepalive",
    )
    print("Baidu Drive credential check complete." if configured
          else "Baidu Drive login is not configured; no credentials touched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
