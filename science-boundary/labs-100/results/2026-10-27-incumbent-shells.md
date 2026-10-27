# 2026-10-27 exact Hamming-shell exclusions around E=578 incumbent

## Center

Public Few Shots / QOBLIB length-100 incumbent:

`++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-`

Exact energy: `578`.

## Radius 1 through 5

Earlier exhaustive enumeration checked every edit at Hamming distance 1, 2, 3, 4, or 5 from the incumbent. Total candidates:

`79,375,495`

No candidate had energy below `578`.

Counts by shell:

| radius | count |
| ---: | ---: |
| 1 | 100 |
| 2 | 4,950 |
| 3 | 161,700 |
| 4 | 3,921,225 |
| 5 | 75,287,520 |

## Radius 6

`code/sphere_shell.cpp` was validated first by reproducing the exact radius-5 count `75,287,520`. On the current local 5-CPU environment the radius-5 regression completed in 10.79 seconds and found shell minimum energy `950`.

The same parallel scanner was then run on the exact radius-6 shell:

```text
BASE energy=578
RADIUS radius=6 tested=1192052400 best=978 seconds=172.064
BESTSEQ -+++++---++++-----++-++--+--++++++++-+---+-++--+++--+--++----+----+-+-+-++---++---++-+-++-+--+--+-+-
```

The candidate count `1,192,052,400` equals `C(100,6)`, so the shell was completely enumerated. Its best energy is `978`, far above the incumbent.

Therefore every sequence at Hamming distance `<=6` from this incumbent has energy at least `578`, with equality attained at the center (and potentially at other already-covered distances) but no improvement.

Total non-center sequences excluded through radius 6:

`1,271,427,895`

Because the eight standard LABS symmetries are Hamming isometries and preserve energy, the same radius-6 exclusion applies around every symmetry image of the incumbent.

## Next exact shell

Radius 7 contains:

`C(100,7) = 16,007,560,800`

candidates. This is roughly 13.4 times the radius-6 work and is suitable for a one-shot parallel GitHub Actions computation. A completed radius-7 scan is scientifically useful even if it finds no breakthrough because it extends the exact local exclusion by an order of magnitude.

## Reproduction

Build:

```bash
g++ -O3 -march=native -fopenmp -DNDEBUG \
  science-boundary/labs-100/code/sphere_shell.cpp -o /tmp/labs100-sphere-shell
```

Then pass the center sequence, radius, and optional OpenMP thread count.
