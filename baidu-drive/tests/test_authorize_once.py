from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import authorize_once  # noqa: E402


class AuthorizeOnceTests(unittest.TestCase):
    def test_oob_authorization_requests_only_netdisk_scope(self):
        url = urllib.parse.urlparse(authorize_once.authorization_url("app-key"))
        self.assertEqual(url.hostname, "openapi.baidu.com")
        qs = urllib.parse.parse_qs(url.query)
        self.assertEqual(qs["response_type"], ["code"])
        self.assertEqual(qs["redirect_uri"], ["oob"])
        self.assertEqual(qs["scope"], ["basic,netdisk"])

    def test_exchange_code_returns_only_bootstrap_refresh_token(self):
        def fake_open(req, timeout):
            form = urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)
            self.assertEqual(form["grant_type"], ["authorization_code"])
            self.assertEqual(form["redirect_uri"], ["oob"])
            self.assertEqual(form["code"], ["code-value"])
            return io.BytesIO(json.dumps({
                "access_token": "access-not-exported",
                "refresh_token": "refresh-secret",
            }).encode())
        with mock.patch.object(authorize_once.urllib.request, "urlopen", side_effect=fake_open):
            self.assertEqual(
                authorize_once.exchange_code("app", "secret", "code-value"),
                {"refresh_token": "refresh-secret"},
            )

    def test_exports_only_dedicated_google_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rclone.conf"
            path.write_text(
                '[unrelated]\ntype=drive\nsecret=do-not-export\n'
                '[bdm-drive]\ntype=drive\nscope=drive.file\n'
                'client_id=client\nclient_secret=secret\n'
                'token={"refresh_token":"token"}\n'
            )
            result = authorize_once.extract_google_remote(path)
            self.assertIn("[bdm-drive]", result)
            self.assertNotIn("do-not-export", result)
            self.assertNotIn("[unrelated]", result)

    def test_github_cli_receives_secret_only_via_stdin(self):
        with mock.patch.object(authorize_once.subprocess, "run") as process:
            authorize_once.set_secret("BAIDU_DRIVE_STATE_KEY", "hidden", "owner/repo")
        args = process.call_args.args[0]
        self.assertNotIn("hidden", args)
        self.assertEqual(process.call_args.kwargs["input"], "hidden")

    def test_rejects_outside_app_root(self):
        with self.assertRaises(ValueError):
            authorize_once.app_root("/BaiduDriveMover")
        self.assertEqual(authorize_once.app_root("/apps/demo"), "/apps/demo")


    def test_device_code_requests_official_scope(self):
        def fake_open(req, timeout):
            url = urllib.parse.urlparse(req.full_url)
            self.assertEqual(url.path, "/oauth/2.0/device/code")
            values = urllib.parse.parse_qs(url.query)
            self.assertEqual(values["response_type"], ["device_code"])
            self.assertEqual(values["scope"], ["basic,netdisk"])
            return io.BytesIO(json.dumps({
                "device_code": "opaque", "user_code": "ABCD",
                "verification_url": "https://openapi.baidu.com/device",
                "qrcode_url": "https://openapi.baidu.com/qr",
                "expires_in": 600, "interval": 2,
            }).encode())
        value = authorize_once.request_device_code("app-key", opener=fake_open)
        self.assertEqual(value["device_code"], "opaque")
        self.assertEqual(value["interval"], 2)
        self.assertEqual(value["user_code"], "ABCD")

    def test_device_login_polls_without_leaking_token(self):
        calls = []
        def fake_open(req, timeout):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)
            self.assertEqual(query["grant_type"], ["device_token"])
            self.assertEqual(query["code"], ["opaque"])
            calls.append(query)
            result = {"error": "authorization_pending"} if len(calls) == 1 else {
                "access_token": "access-token", "refresh_token": "rotated-refresh"
            }
            return io.BytesIO(json.dumps(result).encode())
        now = [0]
        def pause(seconds):
            now[0] += seconds
        auth = authorize_once.wait_for_device_login(
            "app", "secret", {"device_code": "opaque", "interval": 2, "expires_in": 10},
            opener=fake_open, clock=lambda: now[0], pause=pause
        )
        self.assertEqual(auth, {"refresh_token": "rotated-refresh"})
        self.assertEqual(len(calls), 2)

    def test_legacy_http_qr_url_is_upgraded_to_https(self):
        device = {
            "device_code": "opaque", "user_code": "ABCD",
            "verification_url": "https://openapi.baidu.com/device",
            "qrcode_url": "http://openapi.baidu.com/device/qrcode/example",
            "expires_in": 600, "interval": 5,
        }
        with mock.patch.object(authorize_once, "request_device_code", return_value=device), \
             mock.patch.object(authorize_once, "wait_for_device_login", return_value={"refresh_token":"ok"}), \
             mock.patch.object(authorize_once.webbrowser, "open") as opened:
            authorize_once.device_authorize("app", "secret")
        opened.assert_called_once_with("https://openapi.baidu.com/device/qrcode/example")

    def test_device_login_expired_stops(self):
        now = [0]
        def pending(req, timeout):
            return io.BytesIO(b'{"error":"authorization_pending"}')
        def pause(seconds):
            now[0] += seconds
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            authorize_once.wait_for_device_login(
                "app", "secret", {"device_code": "opaque", "interval": 2, "expires_in": 3},
                opener=pending, clock=lambda: now[0], pause=pause
            )

    def test_existing_secrets_prevent_key_rotation(self):
        existing = mock.Mock(stdout=json.dumps([{"name": "BAIDU_DRIVE_STATE_KEY"}]))
        with mock.patch.object(authorize_once.subprocess, "run", return_value=existing):
            with self.assertRaisesRegex(RuntimeError, "already exist"):
                authorize_once.ensure_fresh_install("owner/repo")

    def test_fresh_install_can_continue(self):
        existing = mock.Mock(stdout="[]")
        with mock.patch.object(authorize_once.subprocess, "run", return_value=existing):
            authorize_once.ensure_fresh_install("owner/repo")


if __name__ == "__main__":
    unittest.main()
