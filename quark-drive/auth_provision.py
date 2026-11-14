#!/usr/bin/env python3
"""Ephemeral browser-cookie and rclone credentials for GitHub Actions runners."""
from __future__ import annotations

import argparse
import configparser
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import zipfile

import auth_session
import controller
import auth_cipher

RCLONE_ARCHIVE = "rclone-v1.74.4-linux-amd64.zip"
RCLONE_SHA256 = "fe435e0c36228e7c2f116a8701f01127bb1f694005fc11d1f27186c8bca4115d"
RCLONE_URL = "https://github.com/rclone/rclone/releases/download/v1.74.4/" + RCLONE_ARCHIVE
RCLONE_MEMBER = "rclone-v1.74.4-linux-amd64/rclone"
REMOTE_NAME = "bdm-drive"
REFRESH_MARGIN_SECONDS = 300


class AuthError(RuntimeError):
    pass


def validate_google(config_text: str, state_key: str) -> configparser.SectionProxy:
    auth_cipher.key_bytes(state_key)
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(config_text)
        remote = parser[REMOTE_NAME]
        token = json.loads(remote["token"])
    except (configparser.Error, KeyError, ValueError) as exc:
        raise AuthError("invalid Google Drive rclone configuration") from exc
    if remote.get("type") != "drive" or remote.get("scope") != "drive.file":
        raise AuthError("Google Drive remote must use the drive.file scope")
    if not token.get("refresh_token"):
        raise AuthError("Google Drive remote requires a refresh token")
    return remote


def write_private(path: Path, value: str) -> None:
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8") as handle:
        handle.write(value)


def export_paths(paths: dict[str, str | Path]) -> None:
    output = Path(os.environ["GITHUB_ENV"])
    with output.open("a", encoding="utf-8") as handle:
        for key, value in paths.items():
            handle.write(f"{key}={value}\n")


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


def refresh_google_token(config_path: Path, token_path: Path, freshness_path: Path, rclone_path: Path) -> None:
    if freshness_path.exists() and time.time() + REFRESH_MARGIN_SECONDS < float(freshness_path.read_text()):
        return
    environment = os.environ.copy()
    environment["RCLONE_CONFIG"] = str(config_path)
    result = subprocess.run(
        [str(rclone_path), "lsf", "bdm-drive:", "--max-depth", "1", "--files-only"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env=environment, timeout=90, check=False,
    )
    if result.returncode != 0:
        raise AuthError("Google rclone token validation or refresh failed")
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(config_path.read_text(encoding="utf-8"))
    token = json.loads(parser[REMOTE_NAME]["token"])
    access_token = str(token["access_token"])
    expiry = dt.datetime.fromisoformat(str(token["expiry"]).replace("Z", "+00:00")).timestamp()
    if not access_token or time.time() + REFRESH_MARGIN_SECONDS >= expiry:
        raise AuthError("Google rclone did not return a fresh access token")
    write_private(token_path, access_token)
    write_private(freshness_path, str(expiry))


def provision(mode: str) -> bool:
    initial = os.environ.get("QUARK_DRIVE_QUARK_SESSION", "")
    google = os.environ.get("QUARK_DRIVE_RCLONE_CONFIG", "")
    state_key = os.environ.get("QUARK_DRIVE_STATE_KEY", "")
    if not initial.strip() or not google.strip() or not state_key.strip():
        return False
    auth_session.normalize(initial)
    validate_google(google, state_key)
    gh = controller.GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    session = auth_session.read(gh, initial, state_key)
    if mode == "prepare":
        auth_session.save_if_changed(gh, initial, state_key, session)
    elif mode != "relay":
        raise AuthError("unknown provisioning mode")

    base = Path(os.environ["RUNNER_TEMP"]) / "quark-drive-auth"
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    cookie_path = base / "quark.cookies"
    config_path = base / "rclone.conf"
    key_path = base / "state.key"
    rclone_path = base / "rclone"
    write_private(cookie_path, session)
    write_private(config_path, google)
    write_private(key_path, state_key.strip())
    install_rclone(rclone_path)
    paths: dict[str, str | Path] = {
        "QUARK_DRIVE_BAIDU_AUTH_FILE": cookie_path,
        "QUARK_DRIVE_RCLONE_CONFIG_FILE": config_path,
        "QUARK_DRIVE_RCLONE_BIN": rclone_path,
        "QUARK_DRIVE_STATE_KEY_FILE": key_path,
    }
    if mode == "relay":
        token_path = base / "google.access-token"
        expiry_path = base / "google.token-expiry"
        refresh_google_token(config_path, token_path, expiry_path, rclone_path)
        paths["QUARK_DRIVE_GOOGLE_ACCESS_TOKEN_FILE"] = token_path
        paths["QUARK_DRIVE_GOOGLE_TOKEN_EXPIRY_FILE"] = expiry_path
    export_paths(paths)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "relay"))
    args = parser.parse_args()
    try:
        configured = provision(args.mode)
    except (AuthError, auth_session.SessionError, auth_cipher.CipherError) as exc:
        print(f"Quark Drive runner authentication provisioning failed: {exc}")
        return 1
    print("Runner authentication ready." if configured else "Quark Drive login is not configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
