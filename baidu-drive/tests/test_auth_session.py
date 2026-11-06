from __future__ import annotations

import base64
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth_session  # noqa: E402

KEY = base64.b64encode(b"k" * 32).decode()
INITIAL = "BDUSS=initial; STOKEN=original"
UPDATED = "BDUSS=next; STOKEN=rotated"


class Repo:
    def __init__(self):
        self.state = {}
        self.writes = 0

    def read_json(self, path, default=None):
        return self.state or default, None

    def write_json(self, path, value, message):
        self.state = value
        self.writes += 1


class AuthSessionTests(unittest.TestCase):
    def test_encrypted_state_is_stable_without_cookie_change(self):
        repo = Repo()
        self.assertEqual(auth_session.read(repo, INITIAL, KEY), "BDUSS=initial; STOKEN=original")
        self.assertTrue(auth_session.save_if_changed(repo, INITIAL, KEY, INITIAL))
        self.assertFalse(auth_session.save_if_changed(repo, INITIAL, KEY, INITIAL))
        self.assertEqual(repo.writes, 1)
        self.assertNotIn("STOKEN=", json.dumps(repo.state))

    def test_server_rotated_cookie_survives_vm_replacement(self):
        repo = Repo()
        auth_session.save_if_changed(repo, INITIAL, KEY, INITIAL)
        auth_session.save_if_changed(repo, INITIAL, KEY, UPDATED)
        self.assertEqual(auth_session.read(repo, INITIAL, KEY), "BDUSS=next; STOKEN=rotated")
        self.assertEqual(repo.writes, 2)

    def test_new_local_login_supersedes_previous_rotated_session(self):
        repo = Repo()
        auth_session.save_if_changed(repo, INITIAL, KEY, UPDATED)
        new_login = "BDUSS=human; STOKEN=new-login"
        self.assertEqual(auth_session.read(repo, new_login, KEY), new_login)
        auth_session.save_if_changed(repo, new_login, KEY, new_login)
        self.assertEqual(auth_session.read(repo, new_login, KEY), new_login)

    def test_missing_stoken_is_not_accepted(self):
        with self.assertRaises(auth_session.SessionError):
            auth_session.normalize("BDUSS=only")
        with self.assertRaises(auth_session.SessionError):
            auth_session.normalize("STOKEN=only")


if __name__ == "__main__":
    unittest.main()
