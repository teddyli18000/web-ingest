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


if __name__ == "__main__":
    unittest.main()
