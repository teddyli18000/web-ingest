#!/usr/bin/env python3
"""One-time private OAuth bootstrap; run locally, never in public GitHub Actions.

Requires: authenticated GitHub CLI, a Baidu developer app, and a pre-authorized
Google rclone remote named bdm-drive with scope drive.file.
"""
from __future__ import annotations

import argparse
import base64
import configparser
from getpass import getpass
import json
from pathlib import Path
import secrets
import subprocess
import urllib.parse
import urllib.request
import webbrowser

REPO = "teddyli18000/web-ingest"
BAIDU_AUTHORIZE_URL = "https://openapi.baidu.com/oauth/2.0/authorize"
BAIDU_TOKEN_URL = "https://openapi.baidu.com/oauth/2.0/token"


def authorization_url(client_id: str) -> str:
    query = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": "oob",
        "scope": "basic,netdisk",
    })
    return f"{BAIDU_AUTHORIZE_URL}?{query}"


def exchange_code(client_id: str, client_secret: str, code: str) -> dict[str, str]:
    payload = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "oob",
    }).encode()
    req = urllib.request.Request(
        BAIDU_TOKEN_URL, data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read(65536))
        refresh_token = str(result["refresh_token"])
        access_token = str(result["access_token"])
        if not refresh_token or not access_token:
            raise ValueError("incomplete OAuth response")
    except (OSError, ValueError, KeyError) as exc:
        raise RuntimeError("Baidu OAuth authorization failed; no GitHub Secret was changed") from exc
    return {"refresh_token": refresh_token}


def extract_google_remote(config_path: Path) -> str:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(config_path, encoding="utf-8")
    remote = parser["bdm-drive"]
    if remote.get("type") != "drive" or remote.get("scope") != "drive.file":
        raise ValueError("rclone bdm-drive must be a drive.file-scope Drive remote")
    if not remote.get("client_id"):
        raise ValueError("rclone bdm-drive needs a dedicated OAuth client ID")
    token = json.loads(remote["token"])
    if not token.get("refresh_token"):
        raise ValueError("rclone bdm-drive has no refresh token")
    # Export only our dedicated remote, not unrelated rclone account secrets.
    output = configparser.ConfigParser(interpolation=None)
    output["bdm-drive"] = {key: value for key, value in remote.items()}
    from io import StringIO
    handle = StringIO()
    output.write(handle)
    return handle.getvalue()


def set_secret(name: str, value: str, repo: str = REPO) -> None:
    # gh reads secret bytes from stdin and encrypts them locally, rather than
    # putting credential values into argv or creating persistent plaintext files.
    subprocess.run(
        ["gh", "secret", "set", name, "--repo", repo],
        input=value, text=True, check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def app_root(value: str) -> str:
    if not value.startswith("/apps/") or "/" in value[6:] or ".." in value or any(ch in value for ch in "\\\r\n"):
        raise ValueError("use the app's exact /apps/<app-name> directory")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rclone-config", required=True, type=Path)
    parser.add_argument("--repo", default=REPO)
    args = parser.parse_args()

    google_remote = extract_google_remote(args.rclone_config)
    subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
    client_id = input("Baidu developer App Key: ").strip()
    client_secret = getpass("Baidu developer Secret Key: ").strip()
    root = app_root(input("Baidu app folder (e.g. /apps/MyApp): ").strip())
    if not client_id or not client_secret:
        raise ValueError("Baidu App Key and Secret Key are required")
    link = authorization_url(client_id)
    webbrowser.open(link)
    print("Baidu authorization page:", link)
    code = getpass("Paste the authorization code shown by Baidu: ").strip()
    auth = exchange_code(client_id, client_secret, code)
    bootstrap = json.dumps({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": auth["refresh_token"],
        "app_root": root,
    }, ensure_ascii=False)
    state_key = base64.b64encode(secrets.token_bytes(32)).decode()
    set_secret("BAIDU_DRIVE_BAIDU_OAUTH", bootstrap, args.repo)
    set_secret("BAIDU_DRIVE_RCLONE_CONFIG", google_remote, args.repo)
    set_secret("BAIDU_DRIVE_STATE_KEY", state_key, args.repo)
    print("Three GitHub Actions Secrets installed. Run the Auth Keepalive workflow once to validate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
