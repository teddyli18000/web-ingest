#!/usr/bin/env python3
"""Exhaust classic 5-AND GF(16) inverter topologies against the best legal multiplier support.

The exact rank-9 GF(16) multiplier classification leaves a uniquely strongest
coordinate support

    S* = {1,2,3,4,5,8,10,12,15},

which is one of only two physical right-factor supports requiring five XORs from
four coordinate bits and has the better full operator tradeoff.

This script asks whether three published low-gate 5-AND inverter topologies can,
under any GL(4,2) input basis compatible with the inverse-output space, expose
many of the nine functions r(inv(x)), r in S*, as already-existing wires.

Results (complete over all 20,160 input bases):

* Tay15 (5 AND + 10 XOR): max 4/9, exactly the four formal outputs;
* classic BP16 (5 AND + 11 XOR): max 4/9;
* Jain17 core (5 AND + 12 XOR): max 5/9.

Thus none of these fixed topologies can be a 17-gate inverter+factor package for
S*.  This does not exclude a different free-topology 5-AND/12-linear network.
"""
from __future__ import annotations

import collections
import itertools
import json

SUPPORT = (1,2,3,4,5,8,10,12,15)


def var(i):
    return sum((((x >> i) & 1) << x) for x in range(16))


VARS = [var(i) for i in range(4)]


def lf(mask):
    out = 0
    for i, v in enumerate(VARS):
        if (mask >> i) & 1:
            out ^= v
    return out


def rank(vals):
    piv = []
    for x in vals:
        y = x
        for p in piv:
            y = min(y, y ^ p)
        if y:
            piv.append(y)
            piv.sort(reverse=True)
    return len(piv)


def span(vals):
    out = {0}
    for v in vals:
        out |= {x ^ v for x in tuple(out)}
    return out


def gf16mul(a, b):
    p = 0
    for i in range(4):
        if (b >> i) & 1:
            p ^= a << i
    for d in range(6, 3, -1):
        if (p >> d) & 1:
            p ^= 1 << d
            p ^= 1 << (d - 3)
            p ^= 1 << (d - 4)
    return p & 15


def gfpow(a, n):
    out = 1
    while n:
        if n & 1:
            out = gf16mul(out, a)
        a = gf16mul(a, a)
        n >>= 1
    return out


def inv(a):
    return 0 if a == 0 else gfpow(a, 14)


def target(mask):
    out = 0
    for x in range(16):
        if ((mask & inv(x)).bit_count() & 1):
            out |= 1 << x
    return out


TARGETS = [target(m) for m in SUPPORT]
TARGET_SPACE = span([target(m) for m in (1,2,4,8)])


def tay15(basis):
    m19,m20,m21,m22 = [lf(m) for m in basis]
    w = []
    def e(name, v): w.append((name,v)); return v
    m23=e('M23',m20&m22); m24=e('M24',m19^m20); m25=e('M25',m23^m24)
    m26=e('M26',m21&m25); m27=e('M27',m21^m22); m28=e('M28',m26^m27)
    m29=e('M29',m26^m23); m30=e('M30',m29&m27); m31=e('M31',m22^m30)
    m32=e('M32',m27^m23); m33=e('M33',m19&m32); m34=e('M34',m24^m33)
    m35=e('M35',m23^m34); m36=e('M36',m35&m24); m37=e('M37',m19^m36)
    return w, [m28,m31,m34,m37]


def bp16(basis):
    x1,x2,x3,x4 = [lf(m) for m in basis]
    w=[]
    def e(name,v): w.append((name,v)); return v
    t1=e('t1',x1^x2); t2=e('t2',x1&x3); t3=e('t3',x4^t2); t4=e('t4',t1&t3)
    y4=e('y4',x2^t4); t5=e('t5',x3^x4); t6=e('t6',x2^t2); t7=e('t7',t6&t5)
    y2=e('y2',x4^t7); t8=e('t8',x3^y2); t9=e('t9',t3^y2); t10=e('t10',x4&t9)
    y1=e('y1',t10^t8); t11=e('t11',t3^t10); t12=e('t12',y4&t11); y3=e('y3',t12^t1)
    return w, [y1,y2,y3,y4]


def jain17(basis):
    # Abstracted from verified sbox106_d34.  Free boundary signals are
    # (s41,s48,s49,s51); s50=s41^s48 is the first counted gate.
    a,b,c,d = [lf(m) for m in basis]
    w=[]
    def e(name,v): w.append((name,v)); return v
    s50=e('s50',a^b); s52=e('s52',s50&d); s53=e('s53',c^s52); s54=e('s54',a&s53)
    s55=e('s55',s54^b); s56=e('s56',c^d); s57=e('s57',b^s52); s58=e('s58',s57&s56)
    s59=e('s59',c^s58); s60=e('s60',s53^s59); s61=e('s61',c&s60); s62=e('s62',s53^s61)
    s63=e('s63',s55&s62); s64=e('s64',a^s63); s65=e('s65',s55^s64); s66=e('s66',d^s61)
    s67=e('s67',s65^s66)
    # The complete nine-factor span adds three XORs outside the 17-gate core.
    f86=s59^s66; f87=f86^s64; f88=f87^s67
    factors=[s55,s59,s64,s65,s66,s67,f86,f87,f88]
    return w, factors


def screen(name, build, outputs_from_result):
    compatible=0; best=-1; hist=collections.Counter(); examples=[]
    for basis in itertools.permutations(range(1,16),4):
        if rank(basis)!=4:
            continue
        wires, result = build(basis)
        outputs = outputs_from_result(result)
        if span(outputs) != TARGET_SPACE:
            continue
        compatible += 1
        values={v for _,v in wires}
        hit=sum(t in values for t in TARGETS)
        hist[hit]+=1
        if hit>best:
            best=hit; examples=[(basis,[n for n,v in wires if v in TARGETS])]
        elif hit==best and len(examples)<16:
            examples.append((basis,[n for n,v in wires if v in TARGETS]))
    return {"name":name,"compatible_maps":compatible,"max_direct_coverage":best,
            "coverage_histogram":dict(sorted(hist.items())),"examples":examples}


def main():
    rows=[]
    rows.append(screen('Tay15',tay15,lambda outputs:outputs))
    rows.append(screen('BP16',bp16,lambda outputs:outputs))
    # Jain result is the nine factor set itself; it spans the inverse-output space.
    rows.append(screen('Jain17',jain17,lambda factors:factors))
    assert rows[0]['compatible_maps']==60 and rows[0]['max_direct_coverage']==4
    assert rows[1]['compatible_maps']==60 and rows[1]['max_direct_coverage']==4
    assert rows[2]['compatible_maps']==60 and rows[2]['max_direct_coverage']==5
    print(json.dumps(rows,indent=2))


if __name__=='__main__':
    main()
