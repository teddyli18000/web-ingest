# Few Shots #63 review response — 2026-11-13

Source: https://github.com/few-shots/few-shots/issues/63#issuecomment-6854903128

## Confirmed by both reviewers

- The question A(23,6,10) is established (at least since AVZ 2000 Table II), mathematically well defined, still open, and distinct from prior Few Shots problems.
- Both independent reviews reproduced the 2992-word witness, exact minimum Hamming distance 6, and the certificate hash. The maintained upper bound is 7521.
- The only substantive review blocker is **documented permission to redistribute the complete 2992-word source file and its JSON transcription**. Public availability and the arXiv paper's nonexclusive distribution licence do not establish this.
- Review A requests independently verifiable permission from the authorized rights holder, explicitly covering the full `a23.6.10.2992H` and the JSON transcription. Review B suggests removing unsupported license assertions and keeping original provenance. To satisfy both, obtain the public permission before requesting the next review (max three review cycles per proposal).

## Work performed

- Updated `proposal.md` and `issue-63-ready.md` to describe attribution and the unresolved permission accurately rather than claiming an unverified license.
- Added explicit absolute epsilon = 1.
- Replaced the draft verifier with one that detects duplicate JSON keys, enforces depth <=2, limits integer token lengths, uses bounded reads, rejects symlinks/nonregular files, and retains exact pairwise checks plus the canonical hash format.
- Added `tests/test_verifier_review.py`: 14 regression tests (13 negative/format/canonical plus one valid) passed in a local Python 3.13.5 run before committing. The prior Python 3.12.16 baseline run remains documented in `results/baseline-check.json` for the earlier verifier; the revised verifier has not yet been rechecked against the full baseline in Python 3.12.
- Correct AVZ DOI is https://doi.org/10.1109/18.887851 (not 10.1109/18.887823).

## Required next evidence

A citable permission statement or public record by the person authorized to grant it, indicating that the complete published 2992-word witness and exact/normalized JSON transcription may be redistributed (with attribution if required). The user's statement that attribution is enough is not a substitute for a publicly verifiable source in the referee process. Do not claim this permission exists until evidenced.

## Upstream status

Current upstream #63 has `needs-changes`. GitHub integration previously returned 403 on editing Few Shots issues. The revised `issue-63-ready.md` is a **draft**, not a completed upstream edit. After permission evidence is added, submit one final edit rather than triggering another review prematurely.
