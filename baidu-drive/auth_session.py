"""Baidu browser-session snapshots, encrypted at rest with one serialized writer."""
from __future__ import annotations

import hashlib
import json
from typing import Any

import oauth_state

STATE_PATH = "baidu-drive/state/auth/baidu-session.json"


class SessionError(ValueError):
    pass


def normalize(cookie_header: str) -> str:
    pairs = {}
    for segment in cookie_header.split(";"):
        if "=" in segment:
            name, value = segment.strip().split("=", 1)
            if name:
                pairs[name] = value.strip()
    if not pairs.get("BDUSS") or not pairs.get("STOKEN"):
        raise SessionError("Baidu browser login is required")
    return "; ".join(f"{name}={value}" for name, value in sorted(pairs.items()))


def fingerprint(cookie_header: str) -> str:
    return hashlib.sha256(normalize(cookie_header).encode()).hexdigest()


def read(repo: Any, initial_cookie: str, key: str) -> str:
    initial = normalize(initial_cookie)
    stored, _ = repo.read_json(STATE_PATH, default={})
    if not stored or stored.get("bootstrap_sha256") != fingerprint(initial):
        return initial
    try:
        state = oauth_state.unseal(stored["sealed"], oauth_state.key_bytes(key))
        return normalize(str(state["cookie"]))
    except (KeyError, oauth_state.OAuthError) as exc:
        raise SessionError("encrypted Baidu browser session is unreadable") from exc


def save_if_changed(repo: Any, initial_cookie: str, key: str, latest_cookie: str) -> bool:
    latest = normalize(latest_cookie)
    original = normalize(initial_cookie)
    stored, _ = repo.read_json(STATE_PATH, default={})
    current = read(repo, original, key)
    # Adopt any new human login even when the preceding encrypted state is newer.
    if current == latest and stored.get("bootstrap_sha256") == fingerprint(original):
        return False
    repo.write_json(
        STATE_PATH,
        {
            "schema": 1,
            "bootstrap_sha256": fingerprint(original),
            "sealed": oauth_state.seal({"cookie": latest}, oauth_state.key_bytes(key)),
        },
        "baidu-drive: save encrypted browser session",
    )
    return True
