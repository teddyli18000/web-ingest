#!/usr/bin/env python3
"""Generate multi-output PLA relations for the merged-102 core boundary.

Outputs are the nine factors consumed by q60..q77.  `exact.pla` fixes all
16 core-input states.  `odc-zero.pla` encodes the *complete* fixed-tail ODC:
on core state 0000 every 9-bit factor vector is legal; on states 1..15 the
nine factors are fixed exactly.  The latter uses the relation representation
accepted by ABC `twoexact`: duplicate input minterms with each legal output.

Input bit order in the PLA is q34,q36,q39,q41.  The truth-table evaluator uses
that same order directly rather than relying on integer-string conventions.
"""
import argparse
import itertools
import pathlib

TARGET_NAMES = ["q45", "q59", "q52", "q57", "q53", "q49", "q58", "q55", "q56"]


def target_bits(a, b, c, d):
    q42 = a & b
    q43 = q42 ^ c
    q44 = q43 & d
    q45 = b ^ q44
    q46 = q42 & c
    q47 = d ^ q46
    q48 = a & q47
    q49 = q43 ^ q48
    q50 = q48 ^ b
    q51 = q49 & q50
    q52 = q51 ^ a
    q53 = q52 ^ q49
    q54 = q45 & q53
    q55 = q54 ^ q47
    q56 = q55 ^ q49
    q57 = q53 ^ q45
    q58 = q56 ^ q57
    q59 = q55 ^ q45
    return [q45, q59, q52, q57, q53, q49, q58, q55, q56]


def row(inp, out):
    return "".join(str(x) for x in inp) + " " + "".join(str(x) for x in out)


def write_exact(path):
    lines = [".i 4", ".o 9"]
    for inp in itertools.product((0, 1), repeat=4):
        lines.append(row(inp, target_bits(*inp)))
    lines.append(".e")
    path.write_text("\n".join(lines) + "\n")


def write_odc(path):
    lines = [".i 4", ".o 9"]
    for inp in itertools.product((0, 1), repeat=4):
        if inp == (0, 0, 0, 0):
            for out in itertools.product((0, 1), repeat=9):
                lines.append(row(inp, out))
        else:
            lines.append(row(inp, target_bits(*inp)))
    lines.append(".e")
    path.write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    exact = out / "exact.pla"
    odc = out / "odc-zero.pla"
    write_exact(exact)
    write_odc(odc)
    # exact: 2 header + 16 rows + .e; ODC: replace one row by 512 rows.
    assert len(exact.read_text().splitlines()) == 19
    assert len(odc.read_text().splitlines()) == 530
    print(exact)
    print(odc)


if __name__ == "__main__":
    main()
