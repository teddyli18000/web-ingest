#!/usr/bin/env python3
"""Local browser login for Baidu Drive: persistent Chrome + gh CLI Secrets."""
from __future__ import annotations

import argparse
import base64
import configparser
from io import StringIO
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time

REPO = "teddyli18000/web-ingest"
CHROME_PROFILE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "web-ingest" / "baidu-drive-browser"
SESSION_SECRET = "BAIDU_DRIVE_BAIDU_SESSION"
GOOGLE_SECRET = "BAIDU_DRIVE_RCLONE_CONFIG"
KEY_SECRET = "BAIDU_DRIVE_STATE_KEY"


def cookie_header(cookies: list[dict]) -> str:
    allowed = {}
    for cookie in cookies:
        name, value = str(cookie["name"]), str(cookie["value"])
        if re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", name) and value and ";" not in value and "\n" not in value:
            allowed[name] = value
    if not allowed.get("BDUSS") or not allowed.get("STOKEN"):
        return ""
    return "; ".join(f"{name}={value}" for name, value in sorted(allowed.items()))


def browser_authenticated(context) -> bool:
    response = context.request.post(
        "https://pan.baidu.com/api/gettemplatevariable?channel=chunlei&web=1&app_id=250528&clienttype=0",
        form={"fields": '["username","loginstate"]'},
        timeout=12000,
    )
    if not response.ok:
        return False
    payload = response.json()
    result = payload.get("result") or {}
    return payload.get("errno") == 0 and result.get("loginstate") in (True, 1, "1")


def browser_login(profile: Path = CHROME_PROFILE, timeout_seconds: int = 600) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Install the local browser helper first: python -m pip install playwright") from exc
    profile.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile), channel="chrome", headless=False,
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://pan.baidu.com/disk/home", wait_until="domcontentloaded", timeout=60000)
            print("Use the Chrome window to log into Baidu Netdisk if needed.")
            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                session = cookie_header(context.cookies("https://pan.baidu.com/"))
                if session and browser_authenticated(context):
                    return cookie_header(context.cookies("https://pan.baidu.com/"))
                page.wait_for_timeout(1800)
            raise RuntimeError("Baidu login was not completed")
        finally:
            context.close()


def secret_names(repo: str) -> set[str]:
    result = subprocess.run(
        ["gh", "secret", "list", "--repo", repo, "--json", "name"],
        check=True, text=True, capture_output=True,
    )
    return {entry["name"] for entry in json.loads(result.stdout)}


def set_secret(name: str, value: str, repo: str = REPO) -> None:
    subprocess.run(
        ["gh", "secret", "set", name, "--repo", repo],
        input=value, text=True, check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def extract_google_remote(config_path: Path) -> str:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(config_path, encoding="utf-8")
    remote = parser["bdm-drive"]
    if remote.get("type") != "drive" or remote.get("scope") != "drive.file":
        raise ValueError("The Google rclone remote bdm-drive needs scope drive.file")
    token = json.loads(remote["token"])
    if not token.get("refresh_token"):
        raise ValueError("Google rclone authentication is not complete")
    result = configparser.ConfigParser(interpolation=None)
    result["bdm-drive"] = dict(remote.items())
    handle = StringIO()
    result.write(handle)
    return handle.getvalue()


def google_configuration(config_path: Path) -> str:
    if not config_path.is_file():
        print("Configure Google once in rclone (remote: bdm-drive, type: drive, scope: drive.file).")
        subprocess.run(["rclone", "config"], check=True)
    return extract_google_remote(config_path)


def initialize(repo: str, local_google: Path, login=browser_login, *, google_only: bool = False) -> None:
    subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
    existing = secret_names(repo)
    google = google_configuration(local_google) if google_only or GOOGLE_SECRET not in existing else None
    if google_only:
        subprocess.run(
            ["rclone", "lsjson", "bdm-drive:", "--dirs-only", "--max-depth", "1"],
            check=True, stdout=subprocess.DEVNULL,
        )
    else:
        session = login()
        set_secret(SESSION_SECRET, session, repo)
    if google is not None:
        set_secret(GOOGLE_SECRET, google, repo)
    if not google_only and KEY_SECRET not in existing:
        set_secret(KEY_SECRET, base64.b64encode(secrets.token_bytes(32)).decode(), repo)
    subprocess.run(
        ["gh", "workflow", "run", "cloud-drive-supervisor.yml", "--ref", "main",
         "-f", "reason=auth-updated", "--repo", repo],
        check=True,
    )
    print(
        "Google Drive authorization updated. The master scheduler has been awakened."
        if google_only else
        "Baidu login saved privately. The master scheduler has been awakened."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=REPO)
    parser.add_argument(
        "--rclone-config", type=Path,
        default=Path(os.environ.get("APPDATA", str(Path.home()))) / "rclone" / "rclone.conf",
    )
    parser.add_argument("--google-only", action="store_true", help="refresh the Google Secret without reopening Baidu")
    args = parser.parse_args()
    initialize(args.repo, args.rclone_config, google_only=args.google_only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
