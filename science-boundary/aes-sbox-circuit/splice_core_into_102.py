#!/usr/bin/env python3
"""Splice a synthesized 17-gate core into the merged 102-gate AES certificate.

Input core.json is produced by synth_core17_array_z3.py and must use the fixed
merged-102 core inputs q34,q36,q39,q41.  The script replaces q42..q59 by the
17 new gates, rewrites tail references to the nine required core factors, and
independently checks the resulting 101-gate circuit against arithmetic AES on
all 256 input bytes.
"""
import argparse
import json
import pathlib
import urllib.request

BASE_URL = "https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/huangxin-design/aes102-field-plane-offsets/certificate.json"
MASK256 = (1 << 256) - 1
TARGETS = ["q45", "q59", "q52", "q57", "q53", "q49", "q58", "q55", "q56"]


def fetch_base():
    with urllib.request.urlopen(BASE_URL, timeout=30) as r:
        return json.load(r)


def gate_eval(op, a, b, mask):
    if op == "XOR":
        return a ^ b
    if op == "XNOR":
        return (~(a ^ b)) & mask
    if op == "AND":
        return a & b
    raise ValueError(op)


def aes_mul(a, b):
    r = 0
    for _ in range(8):
        if b & 1:
            r ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return r


def aes_inv(x):
    if x == 0:
        return 0
    r, b, e = 1, x, 254
    while e:
        if e & 1:
            r = aes_mul(r, b)
        b = aes_mul(b, b)
        e >>= 1
    return r


def aes_sbox(x):
    z = aes_inv(x)
    y = 0
    for i in range(8):
        bit = ((z >> i) & 1)
        bit ^= (z >> ((i + 4) & 7)) & 1
        bit ^= (z >> ((i + 5) & 7)) & 1
        bit ^= (z >> ((i + 6) & 7)) & 1
        bit ^= (z >> ((i + 7) & 7)) & 1
        bit ^= (0x63 >> i) & 1
        y |= bit << i
    return y


def evaluate_all(c):
    vals = {}
    for b in range(8):
        t = 0
        for x in range(256):
            if (x >> b) & 1:
                t |= 1 << x
        vals[f"x{b}"] = t
    for g in c["gates"]:
        assert g["a"] in vals and g["b"] in vals, g
        vals[g["out"]] = gate_eval(g["op"], vals[g["a"]], vals[g["b"]], MASK256)
    return vals


def independent_check(c):
    vals = evaluate_all(c)
    outs = [vals[w] for w in c["outputs"]]
    for x in range(256):
        got = sum(((outs[i] >> x) & 1) << i for i in range(8))
        want = aes_sbox(x)
        if got != want:
            return False, {"input": x, "got": got, "want": want}
    return True, None


def splice(base, model):
    assert len(base["gates"]) == 102, len(base["gates"])
    # The merged certificate is named q0.. in topological order; its retained
    # core occupies gate indices 42..59 inclusive.
    assert base["gates"][42]["out"] == "q42"
    assert base["gates"][59]["out"] == "q59"
    assert base["gates"][60]["out"] == "q60"

    new_core = model["gates"]
    mapping = model["target_wire"]
    assert len(new_core) == 17, len(new_core)
    assert set(mapping) == set(TARGETS), mapping
    assert sum(g["op"] == "AND" for g in new_core) == 5

    allowed_prefix = {f"x{i}" for i in range(8)} | {g["out"] for g in base["gates"][:42]}
    produced = set(allowed_prefix)
    for g in new_core:
        assert g["a"] in produced and g["b"] in produced, g
        assert g["out"] not in produced, g["out"]
        produced.add(g["out"])
    for old, new in mapping.items():
        assert old in TARGETS and new in produced

    tail = []
    for g in base["gates"][60:]:
        ng = dict(g)
        ng["a"] = mapping.get(ng["a"], ng["a"])
        ng["b"] = mapping.get(ng["b"], ng["b"])
        tail.append(ng)

    cand = {
        "gates": [dict(g) for g in base["gates"][:42]] + [dict(g) for g in new_core] + tail,
        "outputs": list(base["outputs"]),
    }
    assert len(cand["gates"]) == 101, len(cand["gates"])
    return cand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("core_json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base = fetch_base()
    model = json.load(open(args.core_json))
    cand = splice(base, model)
    ok, err = independent_check(cand)
    if not ok:
        raise SystemExit(f"independent AES check failed: {err}")

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump(cand, open(out, "w"), indent=2)
    print(json.dumps({"gates": 101, "independent_aes_256": True, "output": str(out)}))


if __name__ == "__main__":
    main()
