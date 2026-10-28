#!/usr/bin/env python3
"""Patch the first r4 prototype's single known c4-recovery typo.

The prototype was committed before execution so its derivation could be reviewed.
This helper is intentionally strict: it replaces exactly one known byte-for-byte
fragment and refuses to run if the source has drifted. Workflows compile the
patched temporary copy, never silently editing repository state.
"""
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_search_net2_r4.py INPUT OUTPUT")
src = Path(sys.argv[1]).read_text()
old = '''std::uint64_t mids=s-a-d,qmid=sumq4[i]-a*a-d*d;if(sumsq4[i] < a*a+d*d) throw std::runtime_error("c4 sumsq underflow");
   // x+y=mids; x^2+y^2=qmid => (x-y)^2 = 2*qmid-mids^2.'''
new = '''std::uint64_t mids=s-a-d;std::uint64_t edge_sq=a*a+d*d;if(sumq4[i] < edge_sq)throw std::runtime_error("c4 sumsq underflow");std::uint64_t qmid=sumq4[i]-edge_sq;
   // x+y=mids; x^2+y^2=qmid => (x-y)^2 = 2*qmid-mids^2.'''
note = ' // NOTE typo guard above references sumsq4; use sumq4. (This line is replaced below in repository patch if compiler catches it.)\n'
if src.count(old) != 1:
    raise SystemExit(f"expected exactly one c4 typo fragment, saw {src.count(old)}")
if src.count(note) != 1:
    raise SystemExit(f"expected exactly one prototype note, saw {src.count(note)}")
out = src.replace(old, new).replace(note, '')
if 'sumsq4' in out:
    raise SystemExit('stale sumsq4 identifier remains after patch')
Path(sys.argv[2]).write_text(out)
print('patched exactly one c4 recovery fragment')
