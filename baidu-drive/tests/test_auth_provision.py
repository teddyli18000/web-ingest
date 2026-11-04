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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth_provision  # noqa: E402

KEY = base64.b64encode(b"k" * 32).decode()
RCLONE = """[bdm-drive]
type = drive
scope = drive.file
client_id = test-client.apps.googleusercontent.com
client_secret = test-secret
token = {"access_token":"old","refresh_token":"refresh-google","expiry":"2025-01-01T00:00:00Z"}
"""
STATE = {"access_token": "baidu-access", "app_root": "/apps/demo", "expires_at": 9999999999}


class ProvisionTests(unittest.TestCase):
    def test_google_profile_requires_dedicated_oauth_client(self):
        self.assertEqual(auth_provision.validate_google(RCLONE, KEY)["scope"], "drive.file")
        with self.assertRaises(auth_provision.AuthError):
            auth_provision.validate_google(RCLONE.replace("scope = drive.file", "scope = drive"), KEY)

    def test_google_refresh_is_cached_within_vm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config, token, expiry = root/"rclone.conf", root/"access", root/"expiry"
            config.write_text(RCLONE, encoding="utf-8")
            requests = []
            def fake_open(request, timeout):
                requests.append(request)
                form = urllib.parse.parse_qs(request.data.decode())
                self.assertEqual(form["refresh_token"], ["refresh-google"])
                self.assertEqual(form["grant_type"], ["refresh_token"])
                return io.BytesIO(json.dumps({"access_token":"google-access","expires_in":3600}).encode())
            with mock.patch.object(auth_provision.urllib.request, "urlopen", side_effect=fake_open):
                auth_provision.refresh_google_token(config, token, expiry)
                auth_provision.refresh_google_token(config, token, expiry)
            self.assertEqual(len(requests), 1)
            self.assertEqual(token.read_text(), "google-access")
            self.assertEqual(token.stat().st_mode & 0o077, 0)

    def test_master_uses_rotating_oauth_and_exports_ephemeral_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file=Path(tmp)/"github_env"
            env_file.touch()
            env={"RUNNER_TEMP":tmp,"GITHUB_ENV":str(env_file),
                 "GITHUB_REPOSITORY":"example/repo","GITHUB_TOKEN":"test",
                 "BAIDU_DRIVE_BAIDU_OAUTH":"oauth-bootstrap",
                 "BAIDU_DRIVE_RCLONE_CONFIG":RCLONE,"BAIDU_DRIVE_STATE_KEY":KEY}
            with mock.patch.dict(os.environ,env), mock.patch.object(
                auth_provision.controller,"GitHub",return_value=object()
            ), mock.patch.object(
                auth_provision.oauth_state,"ensure_fresh",return_value=STATE
            ) as rotate, mock.patch.object(auth_provision,"install_rclone"):
                self.assertTrue(auth_provision.provision("prepare"))
            self.assertEqual(rotate.call_args.args[1], "oauth-bootstrap")
            text=env_file.read_text()
            self.assertIn("BAIDU_DRIVE_BAIDU_APP_ROOT=/apps/demo",text)
            self.assertIn("BAIDU_DRIVE_BAIDU_OAUTH_TOKEN_FILE=",text)
            self.assertIn("BAIDU_DRIVE_RCLONE_BIN=",text)
            self.assertNotIn("baidu-access",text)
            self.assertEqual((Path(tmp)/"baidu-drive-auth/baidu.access-token").read_text(),"baidu-access")

    def test_file_worker_reads_without_rotating(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file=Path(tmp)/"github_env";env_file.touch()
            env={"RUNNER_TEMP":tmp,"GITHUB_ENV":str(env_file),
                 "GITHUB_REPOSITORY":"example/repo","GITHUB_TOKEN":"test",
                 "BAIDU_DRIVE_BAIDU_OAUTH":"",
                 "BAIDU_DRIVE_RCLONE_CONFIG":RCLONE,"BAIDU_DRIVE_STATE_KEY":KEY}
            with mock.patch.dict(os.environ,env), mock.patch.object(
                auth_provision.controller,"GitHub",return_value=object()
            ), mock.patch.object(
                auth_provision.oauth_state,"read_fresh",return_value=STATE
            ) as read, mock.patch.object(
                auth_provision,"refresh_google_token"
            ) as google:
                self.assertTrue(auth_provision.provision("relay"))
            read.assert_called_once()
            google.assert_called_once()
            text=env_file.read_text()
            self.assertIn("BAIDU_DRIVE_GOOGLE_ACCESS_TOKEN_FILE=",text)
            self.assertIn("BAIDU_DRIVE_BAIDU_OAUTH_TOKEN_FILE=",text)

    def test_no_secrets_fail_closed(self):
        with mock.patch.dict(os.environ,{"BAIDU_DRIVE_BAIDU_OAUTH":"",
                                        "BAIDU_DRIVE_RCLONE_CONFIG":"",
                                        "BAIDU_DRIVE_STATE_KEY":""}):
            self.assertFalse(auth_provision.provision("prepare"))


if __name__=="__main__":
    unittest.main()
