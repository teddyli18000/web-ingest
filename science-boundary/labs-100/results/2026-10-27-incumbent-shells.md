# 2026-10-27 exact Hamming-shell exclusions around E=578 incumbent

## Center

Public Few Shots / QOBLIB length-100 incumbent:

`++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-`

Exact energy: `578`.

## Radius 1 through 5

Earlier exhaustive enumeration checked every edit at Hamming distance 1, 2, 3, 4, or 5 from the incumbent. Total candidates:

`79,375,495`

No candidate had energy below `578`.

| radius | count |
| ---: | ---: |
| 1 | 100 |
| 2 | 4,950 |
| 3 | 161,700 |
| 4 | 3,921,225 |
| 5 | 75,287,520 |

## Radius 6

`code/sphere_shell.cpp` was validated first by reproducing the exact radius-5 count `75,287,520`. The exact radius-6 shell then produced:

```text
BASE energy=578
RADIUS radius=6 tested=1192052400 best=978 seconds=172.064
BESTSEQ -+++++---++++-----++-++--+--++++++++-+---+-++--+++--+--++----+----+-+-+-++---++---++-+-++-+--+--+-+-
```

The tested count equals `C(100,6)`, so the shell is complete.

## Radius 7

One-shot GitHub Actions run `40561186271` compiled the same durable `code/sphere_shell.cpp` and exhausted the exact radius-7 shell on an Ubuntu hosted runner:

```text
BASE energy=578
RADIUS radius=7 tested=16007560800 best=974 seconds=3433.59
BESTSEQ ++++++--+-+++--+--++-++--+-+++++++++++---+-++---+++-+--++----+--+-+-+-+-++---+++--++---++-++++--+-+-
```

The tested count `16,007,560,800` equals `C(100,7)`, so this shell is also complete. The shell minimum `974` is far above the incumbent.

The uploaded Action artifact was `labs100-radius7` (artifact id `12764907035`). After the result and logs were validated, the disposable workflow was removed from `main`.

## Combined exclusion

Every sequence at ordinary Hamming distance `1..7` from the incumbent has energy strictly above `578`; the center remains the best point in this ball.

Total non-center candidates exhausted through radius 7:

`17,278,988,695`

Because reversal, global negation, and alternating-sign transformation are Hamming isometries and preserve LABS energy, the same radius-7 exclusion applies around every one of the eight standard symmetry images of the incumbent.

At the measured hosted-runner throughput, ordinary radius 8 (`C(100,8)=186,087,894,300`) would take on the order of eleven hours in the current scanner and is not justified by the very high minima at radii 5-7. Subsequent exact work therefore moved to a structure-preserving 50-variable near-skew subspace rather than extending the ordinary Hamming ball blindly.

## Reproduction

Build:

```bash
g++ -O3 -march=native -fopenmp -DNDEBUG \
  science-boundary/labs-100/code/sphere_shell.cpp -o /tmp/labs100-sphere-shell
```

Then pass the center sequence, radius, and optional OpenMP thread count. Always compare `tested=` with `C(100,radius)` before calling a shell complete.
