#!/usr/bin/env python3
"""One-time local OAuth setup. No repository clone or Cookie is required.

Requires GitHub CLI, a Baidu developer application, and an authorized Google
rclone remote named bdm-drive with Drive scope drive.file.
"""
from __future__ import annotations

import argparse
import base64
import configparser
from getpass import getpass
from io import StringIO
import json
from pathlib import Path
import secrets
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

REPO = "teddyli18000/web-ingest"
BAIDU_AUTHORIZE_URL = "https://openapi.baidu.com/oauth/2.0/authorize"
BAIDU_DEVICE_URL = "https://openapi.baidu.com/oauth/2.0/device/code"
BAIDU_TOKEN_URL = "https://openapi.baidu.com/oauth/2.0/token"
SECRET_NAMES = {
    "BAIDU_DRIVE_BAIDU_OAUTH", "BAIDU_DRIVE_RCLONE_CONFIG", "BAIDU_DRIVE_STATE_KEY"
}


def authorization_url(client_id: str) -> str:
    params = urllib.parse.urlencode({
        "response_type": "code", "client_id": client_id,
        "redirect_uri": "oob", "scope": "basic,netdisk",
    })
    return f"{BAIDU_AUTHORIZE_URL}?{params}"


def oauth_get(url: str, parameters: dict[str, str], opener=urllib.request.urlopen) -> dict:
    address = url + "?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(address, method="GET")
    try:
        with opener(request, timeout=30) as response:
            return json.loads(response.read(65536))
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read(65536))
        except (ValueError, UnicodeDecodeError) as cause:
            raise RuntimeError("Baidu OAuth request failed") from cause
    except (OSError, ValueError) as exc:
        raise RuntimeError("Baidu OAuth request failed") from exc


def request_device_code(client_id: str, opener=urllib.request.urlopen) -> dict:
    response = oauth_get(BAIDU_DEVICE_URL, {
        "response_type": "device_code", "client_id": client_id,
        "scope": "basic,netdisk",
    }, opener=opener)
    try:
        code = str(response["device_code"])
        verify_url = str(response["verification_url"])
        expires = int(response["expires_in"])
        interval = max(1, int(response.get("interval", 5)))
        if not code or not verify_url.startswith("https://") or expires <= 0:
            raise ValueError("incomplete device response")
    except (KeyError, ValueError, TypeError) as exc:
        raise RuntimeError("Baidu device authorization unavailable") from exc
    return {
        "device_code": code, "verification_url": verify_url,
        "qrcode_url": str(response.get("qrcode_url") or ""),
        "user_code": str(response.get("user_code") or ""),
        "expires_in": expires, "interval": interval,
    }


def wait_for_device_login(client_id: str, client_secret: str, device: dict,
                          opener=urllib.request.urlopen,
                          clock=time.monotonic, pause=time.sleep) -> dict[str, str]:
    deadline = clock() + device["expires_in"]
    interval = device["interval"]
    while clock() < deadline:
        pause(min(interval, max(0, deadline - clock())))
        response = oauth_get(BAIDU_TOKEN_URL, {
            "grant_type": "device_token", "code": device["device_code"],
            "client_id": client_id, "client_secret": client_secret,
        }, opener=opener)
        if response.get("access_token") and response.get("refresh_token"):
            return {"refresh_token": str(response["refresh_token"])}
        error = str(response.get("error") or response.get("error_description") or "")
        if error in {"authorization_pending", "authorization_waiting", "authorization_pending_error"}:
            continue
        if error == "slow_down":
            interval += 5
            continue
        if error in {"expired_token", "authorization_declined", "access_denied",
                     "authorization_timeout"}:
            raise RuntimeError("Baidu login was declined or expired; rerun setup")
        raise RuntimeError("Baidu device authorization was rejected")
    raise RuntimeError("Baidu device login timed out; rerun setup")


def device_authorize(client_id: str, client_secret: str) -> dict[str, str]:
    device = request_device_code(client_id)
    print("Baidu login: visit", device["verification_url"])
    if device["user_code"]:
        print("Enter code:", device["user_code"])
    qr = urllib.parse.urlsplit(device["qrcode_url"])
    if qr.hostname == "openapi.baidu.com" and qr.scheme in ("http", "https"):
        # The provider sometimes returns an HTTP image URL; open it via HTTPS.
        secure_qr = urllib.parse.urlunsplit(qr._replace(scheme="https"))
        print("QR code:", secure_qr)
        webbrowser.open(secure_qr)
    else:
        webbrowser.open(device["verification_url"])
    print("Confirm authorization in Baidu; this window will detect completion.")
    return wait_for_device_login(client_id, client_secret, device)


def exchange_code(client_id: str, client_secret: str, code: str) -> dict[str, str]:
    result = oauth_get(BAIDU_TOKEN_URL, {
        "grant_type": "authorization_code", "code": code,
        "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": "oob",
    }, opener=urllib.request.urlopen)
    if not result.get("refresh_token") or not result.get("access_token"):
        raise RuntimeError("Baidu authorization failed; no GitHub Secret was changed")
    return {"refresh_token": str(result["refresh_token"])}


def extract_google_remote(config_path: Path) -> str:
    parser = configparser.ConfigParser(interpolation=None)
    with config_path.open(encoding="utf-8") as source:
        parser.read_file(source)
    remote = parser["bdm-drive"]
    if remote.get("type") != "drive" or remote.get("scope") != "drive.file":
        raise ValueError("rclone bdm-drive must be a drive.file-scope Drive remote")
    if not remote.get("client_id"):
        raise ValueError("rclone bdm-drive needs a dedicated OAuth client ID")
    token = json.loads(remote["token"])
    if not token.get("refresh_token"):
        raise ValueError("rclone bdm-drive has no refresh token")
    output = configparser.ConfigParser(interpolation=None)
    output["bdm-drive"] = dict(remote.items())
    handle = StringIO()
    output.write(handle)
    return handle.getvalue()


def set_secret(name: str, value: str, repo: str = REPO) -> None:
    subprocess.run(
        ["gh", "secret", "set", name, "--repo", repo],
        input=value, text=True, check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def ensure_fresh_install(repo: str) -> None:
    result = subprocess.run(
        ["gh", "secret", "list", "--repo", repo, "--json", "name"],
        text=True, check=True, capture_output=True,
    )
    existing = {item["name"] for item in json.loads(result.stdout)}
    if existing & SECRET_NAMES:
        raise RuntimeError("Baidu Drive Secrets already exist. Do not overwrite the AES key or rotated refresh token.")


def app_root(value: str) -> str:
    if not value.startswith("/apps/") or "/" in value[6:] or ".." in value or any(ch in value for ch in "\\\r\n"):
        raise ValueError("use the app's exact /apps/<app-name> directory")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rclone-config", required=True, type=Path)
    parser.add_argument("--repo", default=REPO)
    parser.add_argument("--baidu-login", choices=("device", "code"), default="device")
    args = parser.parse_args()

    google_remote = extract_google_remote(args.rclone_config)
    subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
    ensure_fresh_install(args.repo)
    client_id = input("Baidu developer App Key: ").strip()
    client_secret = getpass("Baidu developer Secret Key: ").strip()
    root = app_root(input("Baidu app folder (e.g. /apps/MyApp): ").strip())
    if not client_id or not client_secret:
        raise ValueError("Baidu App Key and Secret Key are required")
    if args.baidu_login == "device":
        auth = device_authorize(client_id, client_secret)
    else:
        link = authorization_url(client_id)
        webbrowser.open(link)
        print("Baidu authorization page:", link)
        auth = exchange_code(client_id, client_secret,
                             getpass("Paste the one-time Baidu authorization code: ").strip())
    bootstrap = json.dumps({
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": auth["refresh_token"], "app_root": root,
    }, ensure_ascii=False)
    key = base64.b64encode(secrets.token_bytes(32)).decode()
    set_secret("BAIDU_DRIVE_BAIDU_OAUTH", bootstrap, args.repo)
    set_secret("BAIDU_DRIVE_RCLONE_CONFIG", google_remote, args.repo)
    set_secret("BAIDU_DRIVE_STATE_KEY", key, args.repo)
    print("GitHub Actions Secrets installed. Run Baidu Drive Auth Keepalive once.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
