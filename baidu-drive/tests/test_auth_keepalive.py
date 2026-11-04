from __future__ import annotations

import base64
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth_keepalive  # noqa: E402


class KeepaliveTests(unittest.TestCase):
    def test_unconfigured_does_nothing(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            auth_keepalive.oauth_state, "ensure_fresh"
        ) as refresh:
            self.assertFalse(auth_keepalive.maintain(object(), "", "", "", Path(tmp) / "unused"))
            refresh.assert_not_called()

    def test_configured_refreshes_both_without_persisting_google_access_token(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            auth_keepalive.oauth_state, "ensure_fresh"
        ) as baidu, mock.patch.object(
            auth_keepalive.auth_provision, "refresh_google_token"
        ) as google:
            base = Path(tmp) / "auth"
            key = base64.b64encode(b"q" * 32).decode()
            self.assertTrue(auth_keepalive.maintain(object(), "oauth-json", "config", key, base))
            baidu.assert_called_once()
            google.assert_called_once()
            self.assertEqual((base / "google-rclone.conf").read_text(), "config")
            self.assertEqual((base / "google-rclone.conf").stat().st_mode & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
