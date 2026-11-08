from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import authorize_once  # noqa: E402


COOKIE = "BDUSS=example; STOKEN=example"


class AuthorizeOnceTests(unittest.TestCase):
    def test_cookie_header_requires_baidu_session_and_keeps_web_cookies(self):
        cookies = [
            {"name": "STOKEN", "value": "secure", "domain": "pan.baidu.com"},
            {"name": "BDUSS", "value": "account", "domain": ".baidu.com"},
            {"name": "PANWEB", "value": "1", "domain": "pan.baidu.com"},
        ]
        self.assertEqual(
            authorize_once.cookie_header(cookies),
            "BDUSS=account; PANWEB=1; STOKEN=secure",
        )
        self.assertEqual(authorize_once.cookie_header(cookies[:1]), "")

    def test_stale_cookies_do_not_count_as_authenticated(self):
        context = mock.Mock()
        context.request.post.return_value = mock.Mock(
            ok=True, json=lambda: {"errno": 0, "result": {"loginstate": 0}}
        )
        self.assertFalse(authorize_once.browser_authenticated(context))
        context.request.post.return_value = mock.Mock(
            ok=True, json=lambda: {"errno": 0, "result": {"loginstate": 1}}
        )
        self.assertTrue(authorize_once.browser_authenticated(context))
        self.assertIn("fields", context.request.post.call_args.kwargs["form"])

    def test_google_remote_only_exports_dedicated_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"rclone.conf"
            path.write_text(
                "[unrelated]\ntype=drive\nsecret=do-not-export\n"
                "[bdm-drive]\ntype=drive\nscope=drive.file\n"
                "client_id=client\nclient_secret=secret\n"
                'token={"refresh_token":"refresh"}\n',
                encoding="utf-8",
            )
            result = authorize_once.extract_google_remote(path)
            self.assertIn("[bdm-drive]", result)
            self.assertNotIn("unrelated", result)
            self.assertNotIn("do-not-export", result)

    def test_shared_rclone_client_can_be_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rclone.conf"
            path.write_text(
                '[bdm-drive]\ntype=drive\nscope=drive.file\n'
                'token={"refresh_token":"refresh"}\n',
                encoding="utf-8",
            )
            result = authorize_once.extract_google_remote(path)
            self.assertIn("[bdm-drive]", result)
            self.assertNotIn("client_id", result)

    def test_google_only_updates_google_secret_and_preserves_baidu_key(self):
        existing = {authorize_once.SESSION_SECRET, authorize_once.KEY_SECRET, authorize_once.GOOGLE_SECRET}
        with mock.patch.object(
            authorize_once, "secret_names", return_value=existing
        ), mock.patch.object(
            authorize_once, "google_configuration", return_value="[bdm-drive]\n"
        ), mock.patch.object(
            authorize_once, "set_secret"
        ) as set_secret, mock.patch.object(
            authorize_once.subprocess, "run", return_value=mock.Mock(returncode=0)
        ) as run:
            authorize_once.initialize("owner/repo", Path("unused"), login=lambda: self.fail("Baidu login should not run"), google_only=True)
        set_secret.assert_called_once_with(authorize_once.GOOGLE_SECRET, "[bdm-drive]\n", "owner/repo")
        self.assertTrue(any(call.args[0][:2] == ["rclone", "lsjson"] for call in run.call_args_list))
        self.assertIn("reason=auth-updated", run.call_args.args[0])

    def test_initial_setup_writes_three_secrets_then_wakes_master(self):
        with mock.patch.object(
            authorize_once, "secret_names", return_value=set()
        ), mock.patch.object(
            authorize_once, "google_configuration", return_value="[bdm-drive]\n"
        ), mock.patch.object(
            authorize_once, "set_secret"
        ) as set_secret, mock.patch.object(
            authorize_once.subprocess, "run", return_value=mock.Mock(returncode=0)
        ) as run:
            authorize_once.initialize("owner/repo", Path("unused"), login=lambda: COOKIE)
        values = {call.args[0]: call.args[1] for call in set_secret.call_args_list}
        self.assertEqual(values[authorize_once.SESSION_SECRET], COOKIE)
        self.assertIn(authorize_once.KEY_SECRET, values)
        self.assertIn(authorize_once.GOOGLE_SECRET, values)
        self.assertIn("reason=auth-updated", run.call_args.args[0])

    def test_reauthorization_does_not_reset_encryption_key_or_google(self):
        existing = {authorize_once.SESSION_SECRET, authorize_once.KEY_SECRET, authorize_once.GOOGLE_SECRET}
        with mock.patch.object(
            authorize_once, "secret_names", return_value=existing
        ), mock.patch.object(
            authorize_once, "google_configuration"
        ) as google, mock.patch.object(
            authorize_once, "set_secret"
        ) as set_secret, mock.patch.object(
            authorize_once.subprocess, "run", return_value=mock.Mock(returncode=0)
        ):
            authorize_once.initialize("owner/repo", Path("unused"), login=lambda: COOKIE)
        google.assert_not_called()
        set_secret.assert_called_once_with(authorize_once.SESSION_SECRET, COOKIE, "owner/repo")

    def test_secret_write_never_places_cookie_in_argv(self):
        with mock.patch.object(authorize_once.subprocess, "run") as process:
            authorize_once.set_secret(authorize_once.SESSION_SECRET, COOKIE, "owner/repo")
        self.assertNotIn(COOKIE, process.call_args.args[0])
        self.assertEqual(process.call_args.kwargs["input"], COOKIE)


if __name__ == "__main__":
    unittest.main()
