from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.parse

TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR))
import auth_provision  # noqa: E402

COOKIE = "BDUSS=example; STOKEN=example"
KEY = base64.b64encode(b"k" * 32).decode("ascii")
RCLONE = """[bdm-drive]
type = drive
scope = drive.file
client_id = test-client.apps.googleusercontent.com
client_secret = example-secret
token = {"access_token":"old","refresh_token":"refresh-me","expiry":"2025-01-01T00:00:00Z"}
"""


class AuthProvisionTests(unittest.TestCase):
    def test_validated_profile_requires_own_client_and_refresh_token(self):
        section = auth_provision.validate_profile(COOKIE, RCLONE, KEY)
        self.assertEqual(section["scope"], "drive.file")
        with self.assertRaises(auth_provision.AuthError):
            auth_provision.validate_profile("BDUSS=example", RCLONE, KEY)
        with self.assertRaises(auth_provision.AuthError):
            auth_provision.validate_profile(COOKIE, RCLONE.replace("client_id = test-client.apps.googleusercontent.com", "client_id = "), KEY)

    def test_google_refresh_uses_official_grant_and_caches_until_expiry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "rclone.conf"
            token = root / "access"
            expiry = root / "expiry"
            config.write_text(RCLONE, encoding="utf-8")
            calls = []
            def fake_open(request, timeout):
                calls.append(request)
                self.assertEqual(request.full_url, auth_provision.GOOGLE_TOKEN_URL)
                form = urllib.parse.parse_qs(request.data.decode("utf-8"))
                self.assertEqual(form["grant_type"], ["refresh_token"])
                self.assertEqual(form["refresh_token"], ["refresh-me"])
                self.assertEqual(form["client_id"], ["test-client.apps.googleusercontent.com"])
                return io.BytesIO(json.dumps({"access_token": "new-access", "expires_in": 3600}).encode("utf-8"))
            with mock.patch.object(auth_provision.urllib.request, "urlopen", side_effect=fake_open):
                auth_provision.refresh_google_token(config, token, expiry)
                auth_provision.refresh_google_token(config, token, expiry)
            self.assertEqual(len(calls), 1)
            self.assertEqual(token.read_text(), "new-access")
            self.assertLess(token.stat().st_mode & 0o077, 1)

    def test_provision_relay_exports_only_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "github_env"
            env_file.touch()
            env = {
                "RUNNER_TEMP": tmp,
                "GITHUB_ENV": str(env_file),
                "BAIDU_DRIVE_BAIDU_COOKIES": COOKIE,
                "BAIDU_DRIVE_RCLONE_CONFIG": RCLONE,
                "BAIDU_DRIVE_STATE_KEY": KEY,
            }
            with mock.patch.dict(os.environ, env), mock.patch.object(
                auth_provision, "refresh_google_token", side_effect=lambda config, token, expiry: auth_provision.write_private(token, "fresh")
            ):
                self.assertTrue(auth_provision.provision("relay"))
            values = env_file.read_text(encoding="utf-8")
            self.assertIn("BAIDU_DRIVE_BAIDU_AUTH_FILE=", values)
            self.assertIn("BAIDU_DRIVE_GOOGLE_ACCESS_TOKEN_FILE=", values)
            self.assertIn("BAIDU_DRIVE_STATE_KEY_FILE=", values)
            self.assertNotIn("refresh-me", values)
            self.assertNotIn("example-secret", values)
            self.assertEqual((Path(tmp) / "baidu-drive-auth/google.access-token").read_text(), "fresh")

    def test_missing_secrets_do_not_pretend_to_provision(self):
        with mock.patch.dict(os.environ, {
            "BAIDU_DRIVE_BAIDU_COOKIES": "",
            "BAIDU_DRIVE_RCLONE_CONFIG": "",
            "BAIDU_DRIVE_STATE_KEY": "",
        }):
            self.assertFalse(auth_provision.provision("prepare"))


if __name__ == "__main__":
    unittest.main()
