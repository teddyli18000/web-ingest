import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

VERIFIER = Path(__file__).resolve().parents[1] / "code" / "verify.py"
VALID_WORD = (1 << 10) - 1
NEAR_WORD = VALID_WORD ^ 1 ^ (1 << 10)


def test_raw(raw):
    with tempfile.TemporaryDirectory() as temp:
        Path(temp, "certificate.json").write_bytes(raw)
        output = subprocess.check_output([sys.executable, str(VERIFIER), temp], text=True)
        return json.loads(output)


class ReviewTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(test_raw(json.dumps({"codewords": [VALID_WORD]}).encode())["score"], "1")

    def test_duplicate_json_keys(self):
        self.assertFalse(test_raw(b'{"codewords":[],"codewords":[1023]}')["valid"])

    def test_duplicate_codewords(self):
        self.assertFalse(test_raw(json.dumps({"codewords": [VALID_WORD, VALID_WORD]}).encode())["valid"])

    def test_distance(self):
        self.assertFalse(test_raw(json.dumps({"codewords": [VALID_WORD, NEAR_WORD]}).encode())["valid"])

    def test_float(self):
        self.assertFalse(test_raw(b'{"codewords":[1023.0]}')["valid"])

    def test_boolean(self):
        self.assertFalse(test_raw(b'{"codewords":[true]}')["valid"])

    def test_big_integer(self):
        self.assertFalse(test_raw(b'{"codewords":[9999999999999999999999999999]}')["valid"])

    def test_depth(self):
        self.assertFalse(test_raw(b'{"codewords":[[1023]]}')["valid"])

    def test_brackets_in_strings(self):
        self.assertFalse(test_raw(b'{"codewords":"[[][]{}]"}')["valid"])

    def test_wrong_shape(self):
        self.assertFalse(test_raw(b'{"codewords": "bad"}')["valid"])

    def test_oversize(self):
        self.assertFalse(test_raw(b" " * 100001)["valid"])

    def test_canonical_stability(self):
        second = ((1 << 10) - 1) << 10
        a = test_raw(json.dumps({"codewords": [VALID_WORD, second]}).encode())
        b = test_raw(json.dumps({"codewords": [second, VALID_WORD]}).encode())
        self.assertTrue(a["valid"])
        self.assertEqual(a["canonical_hash"], b["canonical_hash"])

    def test_unterminated(self):
        self.assertFalse(test_raw(b'{"codewords":[')["valid"])

    def test_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            target = p / "data.json"
            target.write_text('{"codewords":[1023]}')
            (p / "certificate.json").symlink_to(target)
            output = subprocess.check_output([sys.executable, str(VERIFIER), temp], text=True)
            self.assertFalse(json.loads(output)["valid"])


if __name__ == "__main__":
    unittest.main()
