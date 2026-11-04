#!/usr/bin/env python3
"""Prepare ephemeral OAuth and Drive credentials for the Actions data plane."""
from __future__ import annotations

import argparse
import base64
import configparser
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile

import controller
import oauth_state

RCLONE_ARCHIVE = "rclone-v1.74.4-linux-amd64.zip"
RCLONE_SHA256 = "fe435e0c36228e7c2f116a8701f01127bb1f694005fc11d1f27186c8bca4115d"
RCLONE_URL = "https://downloads.rclone.org/v1.74.4/" + RCLONE_ARCHIVE
RCLONE_MEMBER = "rclone-v1.74.4-linux-amd64/rclone"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
REMOTE_NAME = "bdm-drive"
REFRESH_MARGIN_SECONDS = 300


class AuthError(RuntimeError):
    pass


def validate_google(config_text: str, state_key: str) -> configparser.SectionProxy:
    oauth_state.key_bytes(state_key)
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(config_text)
        remote = parser[REMOTE_NAME]
        token = json.loads(remote["token"])
    except (configparser.Error, KeyError, ValueError) as exc:
        raise AuthError("invalid Google Drive rclone configuration") from exc
    if remote.get("type") != "drive" or remote.get("scope") != "drive.file":
        raise AuthError("Google Drive remote must use the drive.file scope")
    if not remote.get("client_id") or not token.get("refresh_token"):
        raise AuthError("Google Drive remote requires a dedicated OAuth client and refresh token")
    return remote


def write_private(path: Path, value: str) -> None:
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8") as handle:
        handle.write(value)


def export_paths(paths: dict[str, str | Path]) -> None:
    output = Path(os.environ["GITHUB_ENV"])
    with output.open("a", encoding="utf-8") as handle:
        for key, value in paths.items():
            handle.write(f"{key}={value}\n")


def refresh_google_token(config_path: Path, token_path: Path, freshness_path: Path) -> None:
    if freshness_path.exists():
        expiry = float(freshness_path.read_text(encoding="utf-8"))
        if time.time() + REFRESH_MARGIN_SECONDS < expiry:
            return
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(config_path.read_text(encoding="utf-8"))
    remote = parser[REMOTE_NAME]
    original = json.loads(remote["token"])["refresh_token"]
    body = {
        "client_id": remote["client_id"],
        "refresh_token": original,
        "grant_type": "refresh_token",
    }
    if remote.get("client_secret"):
        body["client_secret"] = remote["client_secret"]
    request = urllib.request.Request(
        GOOGLE_TOKEN_URL, data=urllib.parse.urlencode(body).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            issued = json.loads(response.read(65536))
        access_token = str(issued["access_token"])
        expires_in = int(issued["expires_in"])
        if not access_token or expires_in <= REFRESH_MARGIN_SECONDS:
            raise ValueError("invalid token response")
    except (OSError, ValueError, KeyError) as exc:
        raise AuthError("Google access-token refresh failed") from exc
    write_private(token_path, access_token)
    write_private(freshness_path, str(time.time() + expires_in))


def install_rclone(destination: Path) -> None:
    try:
        with urllib.request.urlopen(RCLONE_URL, timeout=120) as response:
            archive = response.read(64 << 20)
        if hashlib.sha256(archive).hexdigest() != RCLONE_SHA256:
            raise AuthError("pinned Linux rclone checksum mismatch")
        with zipfile.ZipFile(io.BytesIO(archive)) as source:
            binary = source.read(RCLONE_MEMBER)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        raise AuthError("pinned Linux rclone download failed") from exc
    destination.write_bytes(binary)
    destination.chmod(0o700)
    result = subprocess.run([str(destination), "version"], capture_output=True, text=True, check=False)
    if result.returncode != 0 or "rclone v1.74.4" not in result.stdout:
        raise AuthError("pinned Linux rclone version check failed")


def provision(mode: str) -> bool:
    config_text = os.environ.get("BAIDU_DRIVE_RCLONE_CONFIG", "")
    state_key = os.environ.get("BAIDU_DRIVE_STATE_KEY", "")
    bootstrap = os.environ.get("BAIDU_DRIVE_BAIDU_OAUTH", "")
    if not config_text.strip() or not state_key.strip() or (mode == "prepare" and not bootstrap.strip()):
        return False
    validate_google(config_text, state_key)
    gh = controller.GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    if mode == "prepare":
        auth = oauth_state.ensure_fresh(gh, bootstrap, state_key)
    elif mode == "relay":
        auth = oauth_state.read_fresh(gh, state_key)
    else:
        raise AuthError("unknown provisioning mode")
    base = Path(os.environ["RUNNER_TEMP"]) / "baidu-drive-auth"
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    baidu_path = base / "baidu.access-token"
    config_path = base / "rclone.conf"
    key_path = base / "state.key"
    write_private(baidu_path, str(auth["access_token"]))
    write_private(config_path, config_text)
    write_private(key_path, state_key.strip())
    paths: dict[str, str | Path] = {
        "BAIDU_DRIVE_BAIDU_OAUTH_TOKEN_FILE": baidu_path,
        "BAIDU_DRIVE_BAIDU_APP_ROOT": str(auth["app_root"]),
        "BAIDU_DRIVE_RCLONE_CONFIG_FILE": config_path,
        "BAIDU_DRIVE_STATE_KEY_FILE": key_path,
    }
    if mode == "prepare":
        rclone_path = base / "rclone"
        install_rclone(rclone_path)
        paths["BAIDU_DRIVE_RCLONE_BIN"] = rclone_path
    else:
        token_path = base / "google.access-token"
        expiry_path = base / "google.token-expiry"
        refresh_google_token(config_path, token_path, expiry_path)
        paths["BAIDU_DRIVE_GOOGLE_ACCESS_TOKEN_FILE"] = token_path
        paths["BAIDU_DRIVE_GOOGLE_TOKEN_EXPIRY_FILE"] = expiry_path
    export_paths(paths)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "relay"))
    args = parser.parse_args()
    try:
        configured = provision(args.mode)
    except (AuthError, oauth_state.OAuthError):
        print("Baidu Drive OAuth provisioning failed.")
        return 1
    print("Baidu Drive ephemeral OAuth files ready." if configured
          else "Baidu Drive OAuth Secrets not configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
