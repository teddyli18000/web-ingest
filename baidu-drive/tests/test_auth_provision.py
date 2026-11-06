from __future__ import annotations

import base64
import configparser
import datetime as dt
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth_provision  # noqa: E402

KEY = base64.b64encode(b"k" * 32).decode()
COOKIE = "BDUSS=baidu; STOKEN=browser"
RCLONE = """[bdm-drive]
type = drive
scope = drive.file
client_id = test-client.apps.googleusercontent.com
client_secret = test-secret
token = {"access_token":"old","refresh_token":"refresh-google","expiry":"2025-01-01T00:00:00Z"}
"""


class ProvisionTests(unittest.TestCase):
    def test_google_profile_requires_drive_file_and_refresh_token(self):
        self.assertEqual(auth_provision.validate_google(RCLONE, KEY)["scope"], "drive.file")
        with self.assertRaises(auth_provision.AuthError):
            auth_provision.validate_google(RCLONE.replace("drive.file", "drive.readonly"), KEY)

    def test_rclone_refresh_is_cached_in_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config, token, expiry = root/"rclone.conf", root/"access", root/"expiry"
            binary = root/"rclone"
            config.write_text(RCLONE, encoding="utf-8")
            calls = []
            def fake_run(args, **kwargs):
                calls.append(args)
                parser = configparser.ConfigParser(interpolation=None)
                parser.read(config, encoding="utf-8")
                token_info = json.loads(parser["bdm-drive"]["token"])
                token_info["access_token"] = "new-access"
                token_info["expiry"] = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat()
                parser["bdm-drive"]["token"] = json.dumps(token_info)
                with config.open("w", encoding="utf-8") as handle:
                    parser.write(handle)
                return mock.Mock(returncode=0)
            with mock.patch.object(auth_provision.subprocess, "run", side_effect=fake_run):
                auth_provision.refresh_google_token(config, token, expiry, binary)
                auth_provision.refresh_google_token(config, token, expiry, binary)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][1:3], ["lsf", "bdm-drive:"])
            self.assertEqual(token.read_text(), "new-access")
            self.assertEqual(token.stat().st_mode & 0o077, 0)

    def test_prepare_provisions_browser_session_privately(self):
        with tempfile.TemporaryDirectory() as tmp:
            envfile = Path(tmp) / "github_env"
            envfile.touch()
            env = {
                "RUNNER_TEMP": tmp, "GITHUB_ENV": str(envfile),
                "GITHUB_REPOSITORY": "example/repo", "GITHUB_TOKEN": "test",
                "BAIDU_DRIVE_BAIDU_SESSION": COOKIE,
                "BAIDU_DRIVE_RCLONE_CONFIG": RCLONE,
                "BAIDU_DRIVE_STATE_KEY": KEY,
            }
            with mock.patch.dict(os.environ, env), mock.patch.object(
                auth_provision.controller, "GitHub", return_value=object()
            ), mock.patch.object(auth_provision.auth_session, "read", return_value=COOKIE), mock.patch.object(
                auth_provision.auth_session, "save_if_changed"
            ) as save, mock.patch.object(auth_provision, "install_rclone"):
                self.assertTrue(auth_provision.provision("prepare"))
            save.assert_called_once()
            text = envfile.read_text()
            self.assertIn("BAIDU_DRIVE_BAIDU_AUTH_FILE=", text)
            self.assertIn("BAIDU_DRIVE_RCLONE_BIN=", text)
            self.assertNotIn("STOKEN=", text)
            self.assertEqual((Path(tmp)/"baidu-drive-auth/baidu.cookies").read_text(), COOKIE)

    def test_relay_reads_latest_session_without_rotating(self):
        with tempfile.TemporaryDirectory() as tmp:
            envfile = Path(tmp)/"github_env"; envfile.touch()
            env = {
                "RUNNER_TEMP": tmp, "GITHUB_ENV": str(envfile),
                "GITHUB_REPOSITORY": "example/repo", "GITHUB_TOKEN": "test",
                "BAIDU_DRIVE_BAIDU_SESSION": COOKIE,
                "BAIDU_DRIVE_RCLONE_CONFIG": RCLONE,
                "BAIDU_DRIVE_STATE_KEY": KEY,
            }
            with mock.patch.dict(os.environ, env), mock.patch.object(
                auth_provision.controller, "GitHub", return_value=object()
            ), mock.patch.object(auth_provision.auth_session, "read", return_value=COOKIE), mock.patch.object(
                auth_provision.auth_session, "save_if_changed"
            ) as save, mock.patch.object(auth_provision, "install_rclone"), mock.patch.object(
                auth_provision, "refresh_google_token"
            ) as refresh:
                self.assertTrue(auth_provision.provision("relay"))
            save.assert_not_called()
            refresh.assert_called_once()

    def test_missing_secrets_block_provisioning(self):
        with mock.patch.dict(os.environ, {"BAIDU_DRIVE_BAIDU_SESSION": "",
                                        "BAIDU_DRIVE_RCLONE_CONFIG": "",
                                        "BAIDU_DRIVE_STATE_KEY": ""}):
            self.assertFalse(auth_provision.provision("prepare"))


if __name__ == "__main__":
    unittest.main()
