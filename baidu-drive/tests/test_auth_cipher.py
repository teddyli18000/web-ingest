from __future__ import annotations

import base64
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth_cipher  # noqa: E402

KEY = base64.b64encode(b"k" * 32).decode()


class CipherTests(unittest.TestCase):
    def test_sealed_browser_session_does_not_expose_cookie(self):
        value = {"cookie": "BDUSS=secret; STOKEN=secret"}
        encoded = auth_cipher.seal(value, auth_cipher.key_bytes(KEY))
        self.assertNotIn("BDUSS", encoded)
        self.assertEqual(auth_cipher.unseal(encoded, auth_cipher.key_bytes(KEY)), value)

    def test_wrong_key_does_not_decrypt(self):
        encoded = auth_cipher.seal({"cookie": "value"}, auth_cipher.key_bytes(KEY))
        with self.assertRaises(auth_cipher.CipherError):
            auth_cipher.unseal(encoded, b"X" * 32)


if __name__ == "__main__":
    unittest.main()
