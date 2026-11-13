import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VerifierTests(unittest.TestCase):
    def verify(self, certificate):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "certificate.json").write_text(json.dumps(certificate))
            completed = subprocess.run([sys.executable, str(ROOT / "code" / "verify.py"), folder],
                                       capture_output=True, text=True, check=True)
            return json.loads(completed.stdout)

    def test_simple_valid(self):
        word = (1 << 10) - 1
        self.assertEqual(self.verify({"codewords": [word]})["score"], "1")

    def test_bad_distance(self):
        first = (1 << 10) - 1
        second = first ^ (1 << 0) ^ (1 << 10)
        self.assertFalse(self.verify({"codewords": [first, second]})["valid"])

    def test_bad_weight(self):
        self.assertFalse(self.verify({"codewords": [1]})["valid"])

    def test_bad_shape(self):
        self.assertFalse(self.verify({"codewords": "hello"})["valid"])


if __name__ == "__main__":
    unittest.main()
