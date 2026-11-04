"""Baidu OAuth refresh and encrypted GitHub state. Only the master may rotate."""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.parse
import urllib.request

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

STATE_PATH = "baidu-drive/state/auth/baidu-oauth.json"
TOKEN_URL = "https://openapi.baidu.com/oauth/2.0/token"
AAD = b"web-ingest/baidu-drive/oauth/v1"
REFRESH_MARGIN = 8 * 24 * 3600


class OAuthError(RuntimeError):
    pass


def key_bytes(encoded: str) -> bytes:
    try:
        value = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise OAuthError("invalid encrypted-state key") from exc
    if len(value) != 32:
        raise OAuthError("encrypted-state key must be 32 bytes")
    return value


def seal(state: dict, key: bytes) -> str:
    nonce = os.urandom(12)
    plain = json.dumps(state, separators=(",", ":")).encode()
    blob = nonce + AESGCM(key).encrypt(nonce, plain, AAD)
    return "v1." + base64.urlsafe_b64encode(blob).decode().rstrip("=")


def unseal(value: str, key: bytes) -> dict:
    if not value.startswith("v1."):
        raise OAuthError("invalid OAuth state version")
    try:
        blob = base64.urlsafe_b64decode(value[3:] + "=" * (-len(value[3:]) % 4))
        state = json.loads(AESGCM(key).decrypt(blob[:12], blob[12:], AAD))
    except (ValueError, TypeError, KeyError, InvalidTag) as exc:
        raise OAuthError("invalid encrypted OAuth state") from exc
    if not isinstance(state, dict):
        raise OAuthError("invalid OAuth state document")
    return state


def parse_bootstrap(encoded: str) -> dict:
    try:
        source = json.loads(encoded)
        result = {name: str(source[name]).strip() for name in
                  ("client_id", "client_secret", "refresh_token", "app_root")}
    except (ValueError, TypeError, KeyError) as exc:
        raise OAuthError("invalid OAuth bootstrap") from exc
    if not all(result.values()):
        raise OAuthError("incomplete OAuth bootstrap")
    if not result["app_root"].startswith("/apps/") or "/" in result["app_root"][6:] or ".." in result["app_root"]:
        raise OAuthError("Baidu application root must be /apps/<app-name>")
    return result


def refresh(client_id: str, client_secret: str, refresh_token: str,
            opener=urllib.request.urlopen, now=None) -> dict:
    params = urllib.parse.urlencode({
        "grant_type": "refresh_token", "client_id": client_id,
        "client_secret": client_secret, "refresh_token": refresh_token,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, params, {"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with opener(req, timeout=30) as resp:
            payload = json.loads(resp.read(65536))
        access, rotated = str(payload["access_token"]), str(payload["refresh_token"])
        ttl = int(payload["expires_in"])
        if not access or not rotated or ttl <= REFRESH_MARGIN:
            raise ValueError("invalid token response")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise OAuthError("Baidu OAuth refresh failed") from exc
    return {"access_token": access, "refresh_token": rotated,
            "expires_at": int(time.time() if now is None else now) + ttl}


def ensure_fresh(repo, bootstrap_json: str, state_key: str,
                 *, now=None, opener=urllib.request.urlopen) -> dict:
    """Called by the serialized master before dispatch; never by file workers."""
    bootstrap = parse_bootstrap(bootstrap_json)
    key = key_bytes(state_key)
    stored, _ = repo.read_json(STATE_PATH, default={})
    previous = unseal(stored["sealed"], key) if stored else {}
    current = int(time.time() if now is None else now)
    if previous and previous.get("app_root") != bootstrap["app_root"]:
        raise OAuthError("Baidu OAuth app root changed after initial authorization")
    if previous and int(previous["expires_at"]) > current + REFRESH_MARGIN:
        return previous
    result = refresh(bootstrap["client_id"], bootstrap["client_secret"],
                     str(previous.get("refresh_token") or bootstrap["refresh_token"]),
                     opener=opener, now=current)
    result["app_root"] = bootstrap["app_root"]
    repo.write_json(STATE_PATH, {"schema": 1, "sealed": seal(result, key)},
                    "baidu-drive: persist rotated encrypted OAuth credentials")
    return result


def read_fresh(repo, state_key: str, *, now=None) -> dict:
    """File workers only read the master-approved access token."""
    stored, _ = repo.read_json(STATE_PATH, default={})
    if not stored:
        raise OAuthError("Baidu OAuth credentials not initialized by master")
    result = unseal(stored["sealed"], key_bytes(state_key))
    if int(result["expires_at"]) <= int(time.time() if now is None else now):
        raise OAuthError("Baidu OAuth access requires master refresh")
    return result
