# Constant-weight code A(23,6,10)

## Question

Maximise the size of a binary constant-weight code with 23 coordinates, exactly 10 ones per word, and minimum pairwise Hamming distance 6. An improved explicit construction gives a new lower bound for A(23,6,10).

## Current state (2026-11-12)

- The [live Brouwer table](https://aeb.win.tue.nl/codes/Andw.html) reports **2992–7521**: a 2992-word published explicit lower-bound construction and a 7521 upper bound (from Agrell–Vardy–Zeger, 2000, per the table's unmarked bound convention).
- Current baseline is the table's [hex code file](https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H): 2992 lines of six-digit hexadecimal values after `$BASE=16`.
- The initial July 2026 improvement (2979) is Christian Lysenstøen's [arXiv:2607.19550](https://arxiv.org/abs/2607.19550), with subsequent polishing by Andries E. Brouwer to 2992. Attribute the baseline to the authors/maintainer and link the source.
- This direction was opened to independently **rebuild and test** the published certificate and to prepare a compliant Few Shots proposal. Baseline automation is pending its initial GitHub Actions run.

## Reproducibility

- `code/verify.py` is the independent, pure-Python 3.12 Few Shots draft verifier. The input is `certificate.json` with `{"codewords":[...integers...]}`. Every integer is a 23-bit weight-10 word. Score = list length, maximise.
- `code/reproduce_baseline.py` downloads the public hex source, requires 2992 distinct weight-10 words, checks 8-subsets independently of the Hamming-distance verifier, writes `baseline/certificate.json`, checks two deliberately broken certificates, and records output/timing in `results/baseline-check.json`.
- `tests/test_verifier.py` covers a trivial valid code, two distinct distance-2 words, wrong weight, and malformed format. Offline test: `python3 -m unittest discover -s tests` from this topic's root.
- A temporary push-triggered Action `.github/workflows/temp-cwc-23-6-10-baseline.yml` performs the source download and writes validated artifacts to this directory. Remove the workflow after verifying its results.

## Why this is a frontier

This is a genuine open cell in the maintained constant-weight code tables, with a large difference between known construction and upper bound. Finding 2993 words would improve a published record and be directly machine-checkable. The upper bound is **not** evidence that 7521 is attainable. A 2026 paper used Johnson decomposition plus maximum-weight independent-set optimisation; exploration should seek genuinely improved coordinated constructions rather than only ruling out small exchanges.

## Next steps

1. Inspect the GitHub Actions result, independent 8-subset test, baseline verifier verdict, timings and SHA-256 hashes. Cross-check the persisted certificate.
2. Add `proposal.md` meeting all eight Few Shots bilingual headings and the verifier evidence. Inspect existing Few Shots proposals again immediately before publication.
3. Show the full proposal to the user before opening a public Few Shots issue under their GitHub account.
4. Optionally begin construction search aiming at 2993+, keeping research notes and exact witnesses.

## Sources and attribution

- [Andries E. Brouwer, live constant-weight table](https://aeb.win.tue.nl/codes/Andw.html); [2992-word source file](https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H).
- [Christian Lysenstøen, *New lower bounds for binary constant-weight codes* (2026)](https://arxiv.org/abs/2607.19550).
- [Agrell, Vardy & Zeger (2000), upper bounds](https://doi.org/10.1109/18.887823).
- [Few Shots propose-a-problem instructions](https://github.com/few-shots/few-shots/blob/main/skills/propose-a-problem/SKILL.md).

Data provenance: published hex code from Brouwer's table, reproduced here with source link and attribution; the user confirmed attribution-permitted reuse. No proprietary or private data is used.

## Work log

- 2026-11-12: verified the table/source links and independent-check design. Four offline smoke tests passed in local Python. Initial 2992-word reconstruction/test delegated to the above temporary Action; do not claim the baseline passed until its result is inspected.
