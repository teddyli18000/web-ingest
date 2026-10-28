# LABS-100 research code

All durable p006 research code lives in this directory. Temporary binaries and raw one-shot logs may live in a runner or local scratch space, but any scientifically useful method/result must be documented back in this topic.

## Exact scorer — `verify.py`

```bash
python3 science-boundary/labs-100/code/verify.py '<100-character +/- sequence>'
```

This scorer is intentionally straightforward and independent of incremental search code.

## Historical unrestricted memetic-tabu reproduction — `memetic.cpp`

Independent reimplementation of the public `lMAts` / 2025 memetic-tabu algorithmic details: population 100, uniform crossover probability 0.9, mutation probability `1/N`, binary tournament selection, random replacement, and short tabu polishing with the published iteration/tenure ranges.

```bash
g++ -O3 -march=native -std=c++20 -fopenmp -DNDEBUG \
  science-boundary/labs-100/code/memetic.cpp -o /tmp/labs100-memetic
/tmp/labs100-memetic --replicas 4 --threads 4 --seconds 600 --seed 1 --target 574
```

Every final sequence is rescored from scratch inside the program. Long campaigns should additionally pipe the final sequence through `verify.py`.

## Unrestricted long-tabu probe — `search.cpp`

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

## Dual-step unrestricted priority queue — `priority_queue.cpp`

Mechanism probe for the second stage of Pšeničnik et al. (arXiv:2409.07222): expand the lowest-energy pivot, add unexplored one-bit neighbors, and add bounded left/right cyclic rotations to cross ordinary bit-flip basins.

```bash
g++ -O3 -march=native -std=c++20 -DNDEBUG \
  science-boundary/labs-100/code/priority_queue.cpp -o /tmp/labs100-pq
/tmp/labs100-pq '<100-character +/- seed>' 5000 3 5000000
```

The command-line values are `Tu`, `Tr`, and an optional cap on distinct states. Current runs use locally chosen tuning and are not presented as exact reproduction of the authors' large-length settings. See `../results/2026-10-27-priority-queue.md`.

## Exact Hamming neighborhoods — `sphere.cpp` and `sphere_shell.cpp`

`sphere.cpp` scans cumulative small radii from 1 through a requested maximum. `sphere_shell.cpp` scans one exact shell and parallelizes over the first flipped position with OpenMP.

```bash
g++ -O3 -march=native -fopenmp -DNDEBUG \
  science-boundary/labs-100/code/sphere_shell.cpp -o /tmp/labs100-sphere-shell
/tmp/labs100-sphere-shell '<100-character +/- sequence>' 6
```

Always validate the reported `tested=` count against `C(100,radius)` before treating a shell as exhausted.

## Exact near-skew crossover cubes — `nearskew_cube.cpp`

For two canonical `(+1,skew99)` N=100 endpoints, enumerate the complete hypercube obtained by independently choosing each differing near-skew free coordinate from either parent. The scanner uses Gray-code incremental correlation updates and periodically recomputes the full energy and structural constraints from scratch.

```bash
g++ -O3 -march=native -std=c++20 -DNDEBUG \
  science-boundary/labs-100/code/nearskew_cube.cpp -o /tmp/nearskew-cube
/tmp/nearskew-cube '<parent-a>' '<parent-b>' 25
```

The optional final argument is the maximum allowed cube dimension; the default is 25. This turns low-dimensional genetic recombination between strong near-skew basins into an exact finite search rather than a heuristic crossover sample.

## Exact near-skew parity-block scans — `nearskew_block.cpp`

After the standard global-sign and alternating-sign normalization `s0=s1=+1`, the canonical near-skew manifold splits into two parity blocks. The `A` block has 25 free coordinates and the `B` block has 24 free coordinates modulo alternating symmetry. This scanner freezes one block and exhausts every assignment of the other.

```bash
g++ -O3 -march=native -std=c++20 -DNDEBUG \
  science-boundary/labs-100/code/nearskew_block.cpp -o /tmp/nearskew-block
/tmp/nearskew-block '<canonical-near-skew-sequence>' A
/tmp/nearskew-block '<canonical-near-skew-sequence>' B
```

It periodically recomputes the exact full energy. A seed whose own energy remains the minimum in both scans is a blockwise global minimum: escaping it inside the near-skew manifold requires changing coordinates in both parity blocks simultaneously.

## Neighboring-length transfer — `cross_length.py` and `delete_to_100.cpp`

`cross_length.py` reproduces targeted insertion/deletion experiments from strong public N=98, N=99, and N=102 sequences. `delete_to_100.cpp` is a fast exact scanner for deleting one through four elements from source lengths 101 through 104, using a packed 128-bit candidate and popcount autocorrelation scoring.

```bash
python3 science-boundary/labs-100/code/cross_length.py

g++ -O3 -march=native -std=c++20 \
  science-boundary/labs-100/code/delete_to_100.cpp -o /tmp/delete-to-100
/tmp/delete-to-100 '<101..104-character +/- source>'
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
