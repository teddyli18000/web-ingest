#!/usr/bin/env python3
"""Fetch Brouwer's 2992-word witness, independently validate, and test the draft verifier."""
import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H"


def independent_check(words):
    """Distance >=6 for weight 10 iff every 8-subset is used at most once."""
    seen = set()
    for word in words:
        assert 0 <= word < (1 << 23) and word.bit_count() == 10
        coords = [i for i in range(23) if word & (1 << i)]
        for subset in itertools.combinations(coords, 8):
            mask = sum(1 << j for j in subset)
            assert mask not in seen, "repeated 8-subset: distance <6"
            seen.add(mask)
    assert len(seen) == 45 * len(words)
    return len(seen)


def main():
    raw = urllib.request.urlopen(URL, timeout=60).read()
    lines = raw.decode("ascii").splitlines()
    assert lines[0] == "$BASE=16"
    assert all(len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s) for s in lines[1:])
    words = [int(s, 16) for s in lines[1:]]
    assert len(words) == 2992 and len(set(words)) == 2992
    t0 = time.perf_counter()
    independent_subsets = independent_check(words)
    independent_sec = time.perf_counter() - t0
    cert = {"codewords": sorted(words)}
    baseline_dir = ROOT / "baseline"
    baseline_dir.mkdir(exist_ok=True)
    (baseline_dir / "certificate.json").write_text(json.dumps(cert, separators=(",", ":")) + "\n")
    cmd = [sys.executable, str(ROOT / "code" / "verify.py")]

    def verify(directory):
        start = time.perf_counter()
        result = subprocess.run(cmd + [str(directory)], capture_output=True, text=True, check=True)
        return json.loads(result.stdout), time.perf_counter() - start

    valid, valid_sec = verify(baseline_dir)
    assert valid["valid"] and valid["score"] == "2992", valid
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        first = words[0]
        bit_on = next(i for i in range(23) if first & (1 << i))
        bit_off = next(i for i in range(23) if not first & (1 << i))
        neighbor = first ^ (1 << bit_on) ^ (1 << bit_off)
        invalid_dist = {"codewords": [first, neighbor]}
        (folder / "certificate.json").write_text(json.dumps(invalid_dist))
        wrong_distance, _ = verify(folder)
        assert not wrong_distance["valid"]
        (folder / "certificate.json").write_text('{"codewords": "wrong-type"}')
        wrong_format, _ = verify(folder)
        assert not wrong_format["valid"]
    result = {
        "source": URL,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "certificate_sha256": hashlib.sha256((baseline_dir / "certificate.json").read_bytes()).hexdigest(),
        "independent_8_subsets": independent_subsets,
        "independent_check_seconds": round(independent_sec, 6),
        "verifier_seconds": round(valid_sec, 6),
        "baseline": valid,
        "broken_distance": wrong_distance,
        "broken_format": wrong_format,
        "python": sys.version.split()[0],
    }
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "baseline-check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
