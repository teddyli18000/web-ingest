# pdfcrack

Sharded search for the **user (open) password** of one locally owned PDF whose
open password was lost. Nothing here is durable; the workflow that drives this
workspace is disposable.

## The target

The file uses the PDF standard security handler, revision 3 / V 2 (RC4,
128-bit key), `EncryptMetadata true`, `/P -4`. An open password is set, so the
document cannot be read at all without it, and the empty password is not valid.

Key derivation is `MD5(padded password || O || P || ID0)` plus 50 rehashes; the
check is the usual 20-pass RC4 verification of `U`. Because `O`, `P` and `ID0`
are per-file salt material, no precomputed table can be reused across files —
the only attack is enumerating candidates. `crack.c` does that at roughly
200k candidates/s on a 4-vCPU runner.

## Files

- `crack.c` — the searcher. Takes the encryption dictionary parameters, a
  charset, a length, an index range and a time budget. OpenMP threads split the
  range into blocks.
- `plan.py` — the ordered list of candidate spaces plus the wave/shard window
  arithmetic. `window` resolves one shard's range; `advance` resolves the next
  wave (or the next space, or a retry with a smaller span after a `BUDGET`).
- `dispatch.sh` — dispatches one wave; used by both the driver and the watcher.
- `watchdog.sh` — restarts the chain when a wave dies without any shard failing.
  On 2026-11-11 one wave ended with `Internal server error. Correlation ID: ...`
  after all 20 shards had succeeded, so the advance job never ran and the chain
  stopped for 21 hours. The window travels in `run-name` (`s= i= p= a=`) so the
  watcher can resume from the right cursor without any repository state.

## Public-repository boundary

The found password is **never** printed, logged, summarised or committed. A hit
is reported as a single integer index inside `[0, base^length)`; the password is
regenerated locally from `(charset, length, index)`. Shard logs contain only
space geometry, progress counts and rates.

## Inputs / outputs

- Inputs: encryption dictionary of the target file, carried as `env` in
  `.github/workflows/temp-pdfcrack.yml`; the PDF itself is never uploaded.
- Outputs: Action logs (`HIT <index>` / `MISS` / `BUDGET`), and the Step Summary
  of the wave run.

## Current state

Spaces already exhausted locally before this workspace existed: common-password
lists (top 10k plus seller/book-derived guesses), digits 1-7, lowercase 1-5.

Planned order is in `plan.py`. Walls: an 8-character lowercase space is already
2.1e11 candidates and a mixed alphanumeric space of the same length is out of
reach at any plausible rate, so this workspace is useful only for the short
spaces near the top of the plan.

## Migration

Nothing here should move into a persistent task. Delete `temp-work/pdfcrack/`
and `.github/workflows/temp-pdfcrack.yml` once the password is recovered or the
plan is abandoned (the weekly cleanup also removes untouched workspaces).
