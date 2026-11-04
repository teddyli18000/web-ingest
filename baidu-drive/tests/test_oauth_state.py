from __future__ import annotations

import base64
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import oauth_state  # noqa: E402

KEY = base64.b64encode(b"x" * 32).decode()
BOOTSTRAP = json.dumps({"client_id": "app", "client_secret": "secret", "refresh_token": "initial", "app_root": "/apps/demo"})


class MemoryRepo:
    def __init__(self):
        self.value = {}
        self.writes = []

    def read_json(self, path, default=None):
        return self.value or default, None

    def write_json(self, path, value, message):
        self.value = value
        self.writes.append((path, message))


class OAuthStateTests(unittest.TestCase):
    def test_sealed_token_roundtrip_and_integrity(self):
        original = {"refresh_token": "sensitive", "access_token": "token", "expires_at": 123}
        sealed = oauth_state.seal(original, oauth_state.key_bytes(KEY))
        self.assertNotIn("sensitive", sealed)
        self.assertEqual(oauth_state.unseal(sealed, oauth_state.key_bytes(KEY)), original)
        with self.assertRaises(oauth_state.OAuthError):
            oauth_state.unseal(sealed, b"y" * 32)

    def test_single_bootstrap_then_rotated_refresh_no_secret_leak(self):
        repo = MemoryRepo()
        calls = []
        def opener(req, timeout):
            args = urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)
            calls.append(args["refresh_token"][0])
            return io.BytesIO(json.dumps({
                "access_token": "access-" + str(len(calls)),
                "refresh_token": "rotated-" + str(len(calls)),
                "expires_in": 30 * 86400,
            }).encode())
        first = oauth_state.ensure_fresh(repo, BOOTSTRAP, KEY, now=1000, opener=opener)
        self.assertEqual(first["refresh_token"], "rotated-1")
        self.assertEqual(first["app_root"], "/apps/demo")
        self.assertEqual(oauth_state.ensure_fresh(repo, BOOTSTRAP, KEY, now=1100, opener=opener), first)
        second = oauth_state.ensure_fresh(repo, BOOTSTRAP, KEY, now=1000 + 30*86400 - oauth_state.REFRESH_MARGIN, opener=opener)
        self.assertEqual(second["refresh_token"], "rotated-2")
        self.assertEqual(calls, ["initial", "rotated-1"])
        self.assertEqual(len(repo.writes), 2)
        self.assertNotIn("rotated-2", json.dumps(repo.value))
        self.assertNotIn("access-2", json.dumps(repo.value))
        self.assertEqual(oauth_state.read_fresh(repo, KEY, now=2000)["access_token"], "access-2")

    def test_failed_refresh_never_writes_token_state(self):
        repo = MemoryRepo()
        def invalid(req, timeout):
            return io.BytesIO(b'{"error":"invalid_grant"}')
        with self.assertRaises(oauth_state.OAuthError):
            oauth_state.ensure_fresh(repo, BOOTSTRAP, KEY, opener=invalid)
        self.assertEqual(repo.writes, [])


if __name__ == "__main__":
    unittest.main()
