#!/usr/bin/env python3
"""Few Shots draft verifier for binary constant-weight A(23,6,10)."""
import hashlib
import json
import sys
from pathlib import Path

N = 23
WEIGHT = 10
MIN_DISTANCE = 6
MAX_WORDS = 10000
MAX_BYTES = 100000


class Invalid(Exception):
    pass


def check(certificate):
    if type(certificate) is not dict or set(certificate) != {"codewords"}:
        raise Invalid("expected an object with the codewords field")
    words = certificate["codewords"]
    if type(words) is not list or not (1 <= len(words) <= MAX_WORDS):
        raise Invalid("invalid codeword list length")
    for word in words:
        if type(word) is not int or not (0 <= word < (1 << N)) or word.bit_count() != WEIGHT:
            raise Invalid("invalid 23-bit weight-10 codeword")
    if len(set(words)) != len(words):
        raise Invalid("duplicate codewords")
    for i, word in enumerate(words):
        for prior in words[:i]:
            if (word ^ prior).bit_count() < MIN_DISTANCE:
                raise Invalid("minimum distance below 6")
    canonical = json.dumps({"codewords": sorted(words)}, separators=(",", ":"))
    return {"valid": True, "score": str(len(words)),
            "canonical_hash": hashlib.sha256(canonical.encode("ascii")).hexdigest(),
            "message": "ok"}


def verify(shot_dir):
    try:
        path = Path(shot_dir) / "certificate.json"
        if path.stat().st_size > MAX_BYTES:
            raise Invalid("certificate too large")
        certificate = json.loads(path.read_text(encoding="utf-8"),
            parse_float=lambda _: (_ for _ in ()).throw(Invalid("noninteger numeric token")),
            parse_constant=lambda _: (_ for _ in ()).throw(Invalid("noninteger numeric token")))
        return check(certificate)
    except (OSError, UnicodeError, ValueError, Invalid, RecursionError):
        return {"valid": False, "score": None, "canonical_hash": None,
                "message": "invalid certificate"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 verify.py <shot_dir>")
    print(json.dumps(verify(sys.argv[1]), separators=(",", ":")))
