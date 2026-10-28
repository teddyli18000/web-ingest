#!/usr/bin/env python3
"""Compute exact per-factor observability don't-cares for the merged 102 tail.

Treat q45,q59,q52,q57,q53,q49,q58,q55,q56 as the boundary outputs of the
18-gate core. For each factor and each of the 16 core-input assignments, flip
that factor on every AES byte having that core assignment, keep the other eight
boundary factors fixed, re-evaluate gates q60 onward, and test all eight final
outputs. This tells whether fixed-tail synthesis really requires exact equality
of each factor on every core state.
"""
import json
import urllib.request

URL = "https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/huangxin-design/aes102-field-plane-offsets/certificate.json"
MASK = (1 << 256) - 1
CORE_INPUTS = ["q34", "q36", "q39", "q41"]
TARGETS = ["q45", "q59", "q52", "q57", "q53", "q49", "q58", "q55", "q56"]
TAIL_START = 60


def op_eval(op, a, b):
    if op == "XOR":
        return a ^ b
    if op == "XNOR":
        return (~(a ^ b)) & MASK
    if op == "AND":
        return a & b
    raise ValueError(op)


def input_tables():
    vals = {}
    for b in range(8):
        t = 0
        for x in range(256):
            if (x >> b) & 1:
                t |= 1 << x
        vals[f"x{b}"] = t
    return vals


def eval_all(c):
    vals = input_tables()
    for g in c["gates"]:
        vals[g["out"]] = op_eval(g["op"], vals[g["a"]], vals[g["b"]])
    return vals


def reeval_tail(c, prefix_vals):
    vals = dict(prefix_vals)
    for g in c["gates"][TAIL_START:]:
        vals[g["out"]] = op_eval(g["op"], vals[g["a"]], vals[g["b"]])
    return vals


def main():
    with urllib.request.urlopen(URL, timeout=30) as r:
        c = json.load(r)
    assert len(c["gates"]) == 102
    assert c["gates"][TAIL_START]["out"] == "q60"
    vals = eval_all(c)
    base_out = [vals[w] for w in c["outputs"]]

    # Map each of the 256 AES bytes to its 4-bit core-input state.
    state_of_x = []
    state_masks = [0] * 16
    for x in range(256):
        s = 0
        for i, w in enumerate(CORE_INPUTS):
            s |= ((vals[w] >> x) & 1) << i
        state_of_x.append(s)
        state_masks[s] |= 1 << x
    assert all(state_masks), [i for i, m in enumerate(state_masks) if not m]

    # Prefix for tail re-evaluation: inputs plus q0..q59, with one target
    # boundary truth table modified at a time.
    prefix = input_tables()
    for g in c["gates"][:TAIL_START]:
        prefix[g["out"]] = vals[g["out"]]

    report = {}
    for target in TARGETS:
        care = 0
        dcare = 0
        changed_examples = {}
        for s in range(16):
            pv = dict(prefix)
            pv[target] ^= state_masks[s]
            tv = reeval_tail(c, pv)
            changed = any(tv[o] != base for o, base in zip(c["outputs"], base_out))
            if changed:
                care |= 1 << s
                # Record one byte/output difference for auditability.
                diffs = []
                for oi, (o, base) in enumerate(zip(c["outputs"], base_out)):
                    delta = tv[o] ^ base
                    if delta:
                        x = (delta & -delta).bit_length() - 1
                        diffs.append((oi, x))
                changed_examples[str(s)] = diffs[:3]
            else:
                dcare |= 1 << s
        report[target] = {
            "care_mask_hex": f"0x{care:04x}",
            "care_states": care.bit_count(),
            "dontcare_mask_hex": f"0x{dcare:04x}",
            "dontcare_states": dcare.bit_count(),
            "changed_examples": changed_examples,
        }

    print(json.dumps({"core_inputs": CORE_INPUTS, "targets": report}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
