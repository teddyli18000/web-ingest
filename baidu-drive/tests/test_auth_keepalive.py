from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth_keepalive  # noqa: E402


class KeepaliveTests(unittest.TestCase):
    def test_unconfigured_does_not_touch_credentials(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            auth_keepalive.auth_session, "read"
        ) as read:
            self.assertFalse(auth_keepalive.maintain(object(), "", "", "", Path(tmp)/"unused"))
            read.assert_not_called()

    def test_configured_maintains_cookie_and_google_grant(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            auth_keepalive.auth_session, "read", return_value="BDUSS=one; STOKEN=two"
        ) as read, mock.patch.object(
            auth_keepalive.auth_session, "save_if_changed"
        ) as save, mock.patch.object(
            auth_keepalive.auth_provision, "install_rclone"
        ) as binary, mock.patch.object(
            auth_keepalive.auth_provision, "refresh_google_token"
        ) as refresh, mock.patch.object(
            auth_keepalive.auth_provision, "validate_google"
        ):
            root = Path(tmp)/"auth"
            self.assertTrue(auth_keepalive.maintain(object(), "BDUSS=one; STOKEN=two", "config", "key", root))
            read.assert_called_once()
            save.assert_called_once()
            binary.assert_called_once()
            refresh.assert_called_once()
            self.assertEqual((root/"google-rclone.conf").read_text(), "config")
            self.assertEqual((root/"google-rclone.conf").stat().st_mode & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
