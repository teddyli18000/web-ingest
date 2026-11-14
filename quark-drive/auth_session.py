"""Quark browser-session snapshots, encrypted at rest with one serialized writer."""
from __future__ import annotations

import hashlib
import json
from typing import Any

import auth_cipher

STATE_PATH = "quark-drive/state/auth/quark-session.json"


class SessionError(ValueError):
    pass


def normalize(cookie_header: str) -> str:
    pairs = {}
    for segment in cookie_header.split(";"):
        if "=" in segment:
            name, value = segment.strip().split("=", 1)
            if name:
                pairs[name] = value.strip()
    if not pairs.get("__puus"):
        raise SessionError("Quark browser login is required")
    return "; ".join(f"{name}={value}" for name, value in sorted(pairs.items()))


def fingerprint(cookie_header: str) -> str:
    return hashlib.sha256(normalize(cookie_header).encode()).hexdigest()


def read(repo: Any, initial_cookie: str, key: str) -> str:
    initial = normalize(initial_cookie)
    stored, _ = repo.read_json(STATE_PATH, default={})
    if not stored or stored.get("bootstrap_sha256") != fingerprint(initial):
        return initial
    try:
        state = auth_cipher.unseal(stored["sealed"], auth_cipher.key_bytes(key))
        return normalize(str(state["cookie"]))
    except (KeyError, auth_cipher.CipherError) as exc:
        raise SessionError("encrypted Quark browser session is unreadable") from exc


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
            "sealed": auth_cipher.seal({"cookie": latest}, auth_cipher.key_bytes(key)),
        },
        "quark-drive: save encrypted browser session",
    )
    return True
