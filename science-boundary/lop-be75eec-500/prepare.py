#!/usr/bin/env python3
"""Decode the exact matrix embedded in the authoritative Few Shots p017 verifier."""
import base64
import importlib.util
import json
from pathlib import Path
import zlib
import hashlib
import sys

root = Path(sys.argv[1])
verifier_path = root / "problems/p017-lop-be75eec-500/verify/verify.py"
spec = importlib.util.spec_from_file_location("p017_verify", verifier_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
raw = zlib.decompress(base64.b64decode(mod.DATA))
assert hashlib.sha256(raw).hexdigest() == "34e940a0ecd9c0a054dfa87c0ad4d2b9286ba141d98be1dcb7ce463fe3f22437"
values = list(map(int, raw.split()))
assert values[0] == 500 and len(values) == 250001, (values[0],len(values))
Path("matrix.txt").write_text(" ".join(map(str,values)))
p=json.loads((root / "problems/p017-lop-be75eec-500/baseline/certificate.json").read_text())["order"]
assert len(p) == 500 and sorted(p) == list(range(500))
Path("baseline.txt").write_text(" ".join(map(str,p)))
M=[values[1+i*500:1+(i+1)*500] for i in range(500)]
score=sum(M[p[i]][p[j]] for i in range(500) for j in range(i+1,500))
assert score == 33489269, score
print("exact instance SHA-256 verified; baseline score:",score)
