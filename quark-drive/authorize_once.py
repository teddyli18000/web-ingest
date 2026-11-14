#!/usr/bin/env python3
"""One-time local Quark login: dedicated Chrome profile -> GitHub Secrets."""
from __future__ import annotations

import argparse
import base64
import configparser
from io import StringIO
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

REPO = "teddyli18000/web-ingest"
PROFILE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "web-ingest" / "quark-drive-browser"
COOKIE_SECRET = "QUARK_DRIVE_QUARK_SESSION"
GOOGLE_SECRET = "QUARK_DRIVE_RCLONE_CONFIG"
KEY_SECRET = "QUARK_DRIVE_STATE_KEY"


def browser_login(timeout_seconds: int = 600) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Install the local browser helper: python -m pip install playwright") from exc
    PROFILE.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(str(PROFILE), channel="chrome", headless=False)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://pan.quark.cn/", wait_until="domcontentloaded", timeout=60000)
            print("Log in to Quark Drive in the dedicated Chrome window.")
            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                cookies = context.cookies(["https://pan.quark.cn", "https://drive-pc.quark.cn"])
                pairs = {c["name"]: c["value"] for c in cookies if c["value"]}
                if pairs.get("__puus"):
                    response = context.request.get(
                        "https://drive-pc.quark.cn/1/clouddrive/file/sort?pr=ucpro&fr=pc&pdir_fid=0&_page=1&_size=1",
                        timeout=15000,
                    )
                    if response.ok and response.json().get("code") == 0:
                        return "; ".join(f"{name}={value}" for name,value in sorted(pairs.items()))
                page.wait_for_timeout(1800)
            raise RuntimeError("Quark Drive login was not completed")
        finally:
            context.close()


def names(repo: str) -> set[str]:
    result = subprocess.run(["gh", "secret", "list", "--repo", repo, "--json", "name"],
                            capture_output=True, text=True, check=True)
    return {row["name"] for row in json.loads(result.stdout)}


def set_secret(name: str, value: str, repo: str):
    subprocess.run(["gh", "secret", "set", name, "--repo", repo], input=value, text=True,
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def google_config(path: Path) -> str:
    source = configparser.ConfigParser(interpolation=None)
    source.read(path, encoding="utf-8")
    remote = source["bdm-drive"]
    token = json.loads(remote["token"])
    if remote.get("type") != "drive" or remote.get("scope") != "drive.file" or not token.get("refresh_token"):
        raise RuntimeError("rclone remote bdm-drive must already have drive.file authorization")
    dest = configparser.ConfigParser(interpolation=None)
    dest["bdm-drive"] = dict(remote.items())
    output = StringIO()
    dest.write(output)
    return output.getvalue()


def initialize(repo: str, config_path: Path, *, google_only: bool = False, login=browser_login):
    subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
    existing = names(repo)
    if not google_only:
        set_secret(COOKIE_SECRET, login(), repo)
    if GOOGLE_SECRET not in existing or google_only:
        set_secret(GOOGLE_SECRET, google_config(config_path), repo)
    if KEY_SECRET not in existing:
        set_secret(KEY_SECRET, base64.b64encode(secrets.token_bytes(32)).decode(), repo)
    subprocess.run(["gh", "workflow", "run", "cloud-drive-supervisor.yml",
                    "--ref", "main", "-f", "reason=auth-updated", "--repo", repo], check=True)
    print("Quark/Google authorization stored privately; shared supervisor notified.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=REPO)
    parser.add_argument("--google-only", action="store_true")
    parser.add_argument("--rclone-config", type=Path, default=Path(os.environ.get("APPDATA", str(Path.home()))) / "rclone" / "rclone.conf")
    args = parser.parse_args()
    initialize(args.repo, args.rclone_config, google_only=args.google_only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
