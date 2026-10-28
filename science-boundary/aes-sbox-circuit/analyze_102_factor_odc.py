#!/usr/bin/env python3
"""Compute the complete boundary ODC of the merged 102-gate AES tail.

Boundary factors:
  q45,q59,q52,q57,q53,q49,q58,q55,q56
Core state:
  (q34,q36,q39,q41) in GF(2)^4.

For each core state, flip each boundary factor on every AES byte having that
state, re-evaluate q60..q101, and encode the resulting eight-output error as a
GF(2) vector.  The nine single-factor error vectors form a linear map from
nine boundary-error bits to all observable tail-output errors at that state.
Its rank/kernel therefore characterizes *all coordinated boundary errors*, not
merely one-factor-at-a-time observability.

Expected exact result:
  state 0000: rank 0, kernel dimension 9 (all factor values are don't-care)
  states 0001..1111: rank 9, kernel dimension 0 (all nine factors exact)
Thus the complete fixed-tail care mask for every factor is 0xfffe, and there
are no hidden multi-factor cancellation don't-cares on nonzero core states.
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


def gf2_rank(vectors):
    pivots = {}
    for x in vectors:
        y = x
        while y:
            p = y.bit_length() - 1
            if p in pivots:
                y ^= pivots[p]
            else:
                pivots[p] = y
                break
    return len(pivots)


def pack_output_delta(tv, base_out, outputs):
    """Pack 8 x 256 output-error bits into one Python integer."""
    z = 0
    for oi, (o, base) in enumerate(zip(outputs, base_out)):
        z |= (tv[o] ^ base) << (256 * oi)
    return z


def main():
    with urllib.request.urlopen(URL, timeout=30) as r:
        c = json.load(r)
    assert len(c["gates"]) == 102
    assert c["gates"][TAIL_START]["out"] == "q60"
    vals = eval_all(c)
    base_out = [vals[w] for w in c["outputs"]]

    # Partition the 256 AES bytes by the four-bit core-input state.
    state_masks = [0] * 16
    state_counts = [0] * 16
    for x in range(256):
        s = 0
        for i, w in enumerate(CORE_INPUTS):
            s |= ((vals[w] >> x) & 1) << i
        state_masks[s] |= 1 << x
        state_counts[s] += 1
    assert all(state_masks), [i for i, m in enumerate(state_masks) if not m]
    # For inversion over GF(16), zero has one preimage and every nonzero norm
    # state appears 17 times in this outer construction.
    assert state_counts[0] == 1, state_counts
    assert all(n == 17 for n in state_counts[1:]), state_counts

    # Prefix for tail re-evaluation: inputs plus q0..q59.  We perturb only the
    # nine boundary factors before evaluating the fixed q60..q101 tail.
    prefix = input_tables()
    for g in c["gates"][:TAIL_START]:
        prefix[g["out"]] = vals[g["out"]]

    target_report = {t: {"care_mask": 0, "dontcare_mask": 0} for t in TARGETS}
    joint_report = []

    for s in range(16):
        columns = []
        examples = {}
        for ti, target in enumerate(TARGETS):
            pv = dict(prefix)
            pv[target] ^= state_masks[s]
            tv = reeval_tail(c, pv)
            delta = pack_output_delta(tv, base_out, c["outputs"])
            columns.append(delta)
            if delta:
                target_report[target]["care_mask"] |= 1 << s
                # One concrete changed output/byte pair for auditability.
                found = None
                for oi, (o, base) in enumerate(zip(c["outputs"], base_out)):
                    d = tv[o] ^ base
                    if d:
                        x = (d & -d).bit_length() - 1
                        found = {"output_index": oi, "byte": x}
                        break
                examples[target] = found
            else:
                target_report[target]["dontcare_mask"] |= 1 << s

        rnk = gf2_rank(columns)
        kernel_dim = 9 - rnk

        # Enumerate all nonzero coordinated factor-error masks in the kernel.
        # There are at most 511, so this is tiny and gives a concrete exhaustive
        # check that rank 9 really means no hidden cancellation pattern.
        nonzero_kernel = []
        for emask in range(1, 1 << 9):
            d = 0
            for i, col in enumerate(columns):
                if (emask >> i) & 1:
                    d ^= col
            if d == 0:
                nonzero_kernel.append(emask)

        assert len(nonzero_kernel) == (1 << kernel_dim) - 1
        joint_report.append(
            {
                "state": s,
                "state_bits": f"{s:04b}",
                "preimage_count": state_counts[s],
                "single_factor_error_rank": rnk,
                "kernel_dimension": kernel_dim,
                "nonzero_kernel_count": len(nonzero_kernel),
                "nonzero_kernel_masks_hex": [f"0x{x:03x}" for x in nonzero_kernel],
                "changed_examples": examples,
            }
        )

    targets_json = {}
    for target, r in target_report.items():
        care = r["care_mask"]
        dcare = r["dontcare_mask"]
        targets_json[target] = {
            "care_mask_hex": f"0x{care:04x}",
            "care_states": care.bit_count(),
            "dontcare_mask_hex": f"0x{dcare:04x}",
            "dontcare_states": dcare.bit_count(),
        }
        assert care == 0xFFFE, (target, hex(care))
        assert dcare == 0x0001, (target, hex(dcare))

    ranks = [r["single_factor_error_rank"] for r in joint_report]
    kernel_dims = [r["kernel_dimension"] for r in joint_report]
    assert ranks == [0] + [9] * 15, ranks
    assert kernel_dims == [9] + [0] * 15, kernel_dims
    assert joint_report[0]["nonzero_kernel_count"] == 511
    assert all(r["nonzero_kernel_count"] == 0 for r in joint_report[1:])

    result = {
        "core_inputs": CORE_INPUTS,
        "state_counts": state_counts,
        "targets": targets_json,
        "joint_state_report": joint_report,
        "complete_characterization": {
            "state_0000": "all 9 boundary error bits are unobservable",
            "states_0001_to_1111": "boundary error map has rank 9; only zero error is unobservable",
            "safe_target_care_mask_hex": "0xfffe",
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
