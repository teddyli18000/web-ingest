# LABS-100 search code

All durable p006 research code lives in this directory.

## Exact scorer

```bash
python3 science-boundary/labs-100/code/verify.py '<100-character +/- sequence>'
```

The scorer is intentionally straightforward and independent of the incremental search kernel.

## Tabu search

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

Modes:

- `random`: independent random starting sequences.
- `incumbent`: 10-40 random flips from the public energy-578 sequence.
- `mixed`: alternates random and incumbent-perturbed starts.

The process exits 0 only if it reaches `--target` (default 574); failure to reach the target is therefore not a correctness failure. Capture output and exit status separately in experiments.

Record meaningful campaigns under `../results/` with exact parameters, code commit, and best independently rescored sequence.
