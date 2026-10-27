# LABS-100 research code

All durable p006 research code lives in this directory. Temporary binaries and raw one-shot logs may live in a runner or local scratch space, but any scientifically useful method/result must be documented back in this topic.

## Exact scorer — `verify.py`

```bash
python3 science-boundary/labs-100/code/verify.py '<100-character +/- sequence>'
```

This scorer is intentionally straightforward and independent of incremental search code.

## Unrestricted tabu probe — `search.cpp`

Optimized build:

```bash
g++ -O3 -march=native -fopenmp -DNDEBUG \
  science-boundary/labs-100/code/search.cpp -o /tmp/labs100-search
```

Debug build with periodic full-energy consistency checks:

```bash
g++ -O2 -fopenmp \
  science-boundary/labs-100/code/search.cpp -o /tmp/labs100-search-debug
```

Example:

```bash
/tmp/labs100-search --runs 200 --steps 300000 --threads 4 --seed 1 --mode mixed
```

Modes include random starts, incumbent perturbations, an explicitly supplied `--start`, and perturbations of a supplied start. The current long-walk design is a calibration tool; `../results/2026-10-27-search-benchmarks.md` shows it is not competitive enough for a large compute campaign unchanged.

## Exact Hamming neighborhoods — `sphere.cpp` and `sphere_shell.cpp`

`sphere.cpp` scans cumulative small radii from 1 through a requested maximum. `sphere_shell.cpp` scans one exact shell and parallelizes over the first flipped position with OpenMP.

```bash
g++ -O3 -march=native -fopenmp -DNDEBUG \
  science-boundary/labs-100/code/sphere_shell.cpp -o /tmp/labs100-sphere-shell
/tmp/labs100-sphere-shell '<100-character +/- sequence>' 6
```

Always validate the reported `tested=` count against `C(100,radius)` before treating a shell as exhausted.

## Neighboring-length transfer — `cross_length.py`

Reproduces targeted insertion/deletion experiments from strong public `N=98`, `N=99`, and `N=102` sequences:

```bash
python3 science-boundary/labs-100/code/cross_length.py
```

See `../results/2026-10-27-cross-length.md`.

## Isolated-subsystem probe — `isosubsys.cpp`

Independent experimental implementation of the `n=4` kicked-descent idea in Lau & Gangat, arXiv:2610.14361v2. It is not the authors' source code and should not be described as an exact implementation-equivalence claim.

```bash
g++ -O3 -march=native -fopenmp -DNDEBUG \
  science-boundary/labs-100/code/isosubsys.cpp -o /tmp/labs100-isosubsys
/tmp/labs100-isosubsys --runs 16 --threads 4 --evals 1000000 --mode random
```

Calibration at N=100 was poor; preserve it as a falsified direction rather than scaling it up blindly.

## Result discipline

Any candidate with energy `<=574` must be rescored by `verify.py` and then by the Few Shots verifier. Record meaningful campaigns under `../results/` with exact parameters, code commit, full candidate sequence when relevant, and enough evidence to distinguish a completed exact search from a timed-out heuristic run.
