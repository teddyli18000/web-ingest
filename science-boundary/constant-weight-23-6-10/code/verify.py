#!/usr/bin/env python3
"""Few Shots draft verifier for binary constant-weight A(23,6,10)."""

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

N = 23
WEIGHT = 10
MIN_DISTANCE = 6
MAX_WORDS = 10000
MAX_BYTES = 100000
MAX_DEPTH = 2
MAX_INT_DIGITS = 12


class Invalid(Exception):
    pass


def check_depth(text):
    depth = 0
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise Invalid("JSON nesting exceeds limit")
        elif char in "]}":
            depth -= 1
    # The JSON decoder validates matching brackets and strings.


def reject_token(_):
    raise Invalid("noninteger numeric token")


def bounded_int(token):
    if len(token.lstrip("-")) > MAX_INT_DIGITS:
        raise Invalid("integer token exceeds limit")
    return int(token)


def unique_keys(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise Invalid("duplicate JSON key")
        result[name] = value
    return result


def read_certificate(shot_dir):
    path = Path(shot_dir) / "certificate.json"
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise Invalid("certificate is not a regular file")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            data = handle.read(MAX_BYTES + 1)
    finally:
        os.close(fd)
    if len(data) > MAX_BYTES:
        raise Invalid("certificate exceeds byte limit")
    return data


def parse_certificate(data):
    text = data.decode("utf-8")
    check_depth(text)
    return json.loads(text, parse_int=bounded_int, parse_float=reject_token,
                      parse_constant=reject_token, object_pairs_hook=unique_keys)


def check(certificate):
    if type(certificate) is not dict or set(certificate) != {"codewords"}:
        raise Invalid("expected a single codewords field")
    words = certificate["codewords"]
    if type(words) is not list or not (1 <= len(words) <= MAX_WORDS):
        raise Invalid("codewords must be a nonempty bounded list")
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
        certificate = parse_certificate(read_certificate(shot_dir))
        return check(certificate)
    except (OSError, UnicodeError, ValueError, Invalid, RecursionError):
        return {"valid": False, "score": None, "canonical_hash": None,
                "message": "invalid certificate"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 verify.py <shot_dir>")
    print(json.dumps(verify(sys.argv[1]), separators=(",", ":")))
