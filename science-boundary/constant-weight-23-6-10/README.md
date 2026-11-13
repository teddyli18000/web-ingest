# Constant-weight code A(23,6,10)

## Question

Maximise the size of a binary constant-weight code with 23 coordinates, exactly 10 ones per word, and minimum pairwise Hamming distance 6. An improved explicit construction gives a new lower bound for A(23,6,10).

## Current state (2026-11-12)

- The [live Brouwer table](https://aeb.win.tue.nl/codes/Andw.html) reports **2992–7521**: a 2992-word published explicit lower-bound construction and a 7521 upper bound (from Agrell–Vardy–Zeger, 2000, per the table's unmarked bound convention).
- Current baseline is the table's [hex code file](https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H): 2992 lines of six-digit hexadecimal values after `$BASE=16`.
- The initial July 2026 improvement (2979) is Christian Lysenstøen's [arXiv:2607.19550](https://arxiv.org/abs/2607.19550), with subsequent polishing by Andries E. Brouwer to 2992. Attribute the baseline to the authors/maintainer and link the source.
- This direction was opened to independently **rebuild and test** the published certificate and to prepare a compliant Few Shots proposal. The published 2992-word source witness was independently reconstructed and verified on GitHub Actions run 43370484174. No improved code is claimed.

## Reproducibility

- `code/verify.py` is the independent, pure-Python 3.12 Few Shots draft verifier. The input is `certificate.json` with `{"codewords":[...integers...]}`. Every integer is a 23-bit weight-10 word. Score = list length, maximise.
- `code/reproduce_baseline.py` downloads the public hex source, requires 2992 distinct weight-10 words, checks 8-subsets independently of the Hamming-distance verifier, writes `baseline/certificate.json`, checks two deliberately broken certificates, and records output/timing in `results/baseline-check.json`.
- `tests/test_verifier.py` covers a trivial valid code, two distinct distance-2 words, wrong weight, and malformed format. Offline test: `python3 -m unittest discover -s tests` from this topic's root.
- [GitHub Actions run 43370484174](https://github.com/teddyli18000/web-ingest/actions/runs/43370484174) performed the one-shot download, tests, and commit. Its temporary workflow was removed after success; rerun the script manually for reproduction.

## Confirmed baseline (2026-11-12)

- Exactly **2992** distinct length-23 weight-10 words, minimum pairwise distance **6** across **4,474,536** pairs. The committed artifact was independently rechecked after the successful Action.
- Independent 8-subset incidence test: **134,640** distinct 8-subsets; any repeated 8-subset would imply an illegal distance.
- Python 3.12.16: full verifier **0.144648 s**; independent check **0.078614 s**; two invalid cases rejected; four unit tests passed.
- Artifacts: [baseline/certificate.json](baseline/certificate.json), [results/baseline-check.json](results/baseline-check.json), [proposal.md](proposal.md).
- Source SHA-256: `5e1f5aa477db162cc46705b4135dbd48878d0640c73492ec63615d1305f0d934`; canonical certificate SHA-256: `6451ae0eb1887314ef32dea943da4ed879f2d7c440115980708e56cf0c4ed9c4`.

## Why this is a frontier

This is a genuine open cell in the maintained constant-weight code tables, with a large difference between known construction and upper bound. Finding 2993 words would improve a published record and be directly machine-checkable. The upper bound is **not** evidence that 7521 is attainable. A 2026 paper used Johnson decomposition plus maximum-weight independent-set optimisation; exploration should seek genuinely improved coordinated constructions rather than only ruling out small exchanges.

## Few Shots proposal submission

- [Few Shots issue #63](https://github.com/few-shots/few-shots/issues/63) was created by the user. Its first eight problem sections and confirmation boxes are present, but the title is incomplete and the Agent check is missing.
- [issue-63-ready.md](issue-63-ready.md) preserves the issue's live body, inserts the exact verified Agent check appendix before the Confirm section, and retains all three checked confirmations.
- The linked GitHub integration returned `403 Resource not accessible by integration` on updating this external repository's issue. The remaining manual action is to replace the issue body with `issue-63-ready.md` and set the title to: `[出题 · Proposal] 二进制常重量码 A(23,6,10)：超过 2992 码字 / Constant-weight code A(23,6,10)`.

## Next steps

1. Present [proposal.md](proposal.md) to the user and obtain approval before posting a public Few Shots issue under their account.
2. Re-check the live record and all Few Shots proposals immediately before issue creation; address referee feedback if submitted.
3. Explore genuinely constructive methods for **2993+**, preserving reproducible search code and any exact new witnesses.

## Sources and attribution

- [Andries E. Brouwer, live constant-weight table](https://aeb.win.tue.nl/codes/Andw.html); [2992-word source file](https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H).
- [Christian Lysenstøen, *New lower bounds for binary constant-weight codes* (2026)](https://arxiv.org/abs/2607.19550).
- [Agrell, Vardy & Zeger (2000), upper bounds](https://doi.org/10.1109/18.887823).
- [Few Shots propose-a-problem instructions](https://github.com/few-shots/few-shots/blob/main/skills/propose-a-problem/SKILL.md).

Data provenance: published hex code from Brouwer's table, reproduced here with source link and attribution; the user confirmed attribution-permitted reuse. No proprietary or private data is used.

## Work log

- 2026-11-12: verified the table/source links and independent-check design. Four offline smoke tests passed in local Python.
- 2026-11-12: GitHub Actions run 43370484174 independently reconstructed the 2992-word source and passed all checks; the saved certificate was then independently inspected over all 4,474,536 pairs. Disposable workflow removed after successful preservation.
