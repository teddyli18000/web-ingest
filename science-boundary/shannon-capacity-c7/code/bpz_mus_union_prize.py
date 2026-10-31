#!/usr/bin/env python3
"""Exact real 10D prize on the union of the first 200 joint-injection MUSes.

Run 41234066014 enumerated 200 deletion-minimal failures of the joint factor/
product injection.  Their union involves only 29 distinct five-dimensional
factor coordinates.  This wrapper reuses the independently replayed exact
terminal-prize engine on two nested universes:
  * mus29: exactly those 29 factor coordinates;
  * owner-shell: all outside support<=3 factors whose exact support is contained
    in the owner union of mus29.
Any positive exact gain is materialized as a Few Shots certificate by the
workflow.  A zero optimum only closes these focused universes.
"""
from __future__ import annotations

import bpz_joint_core_shell_prize as P

MUS_FACTORS=(
1012,1025,1285,1299,1503,1504,1517,1552,1559,1986,3413,3709,3722,3765,
3813,6500,6501,8559,8605,10959,13064,13066,13067,13109,13359,15418,15465,
15467,15759)

P.CORE_FACTORS=MUS_FACTORS
P.SOURCE_CORE_RUN=41234066014

if __name__=='__main__':
    P.main()
