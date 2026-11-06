"""Small AES-256-GCM codec for opaque browser-session state."""
from __future__ import annotations

import base64
import json
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AAD = b"web-ingest/baidu-drive/oauth/v1"


class CipherError(ValueError):
    pass


def key_bytes(encoded: str) -> bytes:
    try:
        key = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise CipherError("invalid encrypted-state key") from exc
    if len(key) != 32:
        raise CipherError("encrypted-state key must be 32 bytes")
    return key


def seal(value: dict, key: bytes) -> str:
    nonce = os.urandom(12)
    data = json.dumps(value, separators=(",", ":")).encode("utf-8")
    blob = nonce + AESGCM(key).encrypt(nonce, data, AAD)
    return "v1." + base64.urlsafe_b64encode(blob).decode("ascii").rstrip("=")


def unseal(value: str, key: bytes) -> dict:
    if not value.startswith("v1."):
        raise CipherError("invalid encrypted-state version")
    try:
        encoded = value[3:]
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        decoded = json.loads(AESGCM(key).decrypt(raw[:12], raw[12:], AAD))
    except (ValueError, TypeError, KeyError, InvalidTag) as exc:
        raise CipherError("invalid encrypted-state ciphertext") from exc
    if not isinstance(decoded, dict):
        raise CipherError("expected encrypted JSON object")
    return decoded
