# AGENTS.md — workflows

Workflow files are thin orchestration layers. Keep collection/conversion logic in the corresponding task directory and repository-wide validation logic in `tools/`.

## Before changing a recurring workflow

1. Read the task README and current workflow, or the registered ownership README for repository-wide maintenance.
2. Read `tools/README.md` and the workflow operations README in this directory.
3. Run or reason against `tools/check-repository-integrity.py --show` before choosing a cron.
4. Preserve load balance: do not overlap another recurring workflow's declared timeout window plus repository buffer.
5. Update task or maintenance documentation when the schedule or behavior changes.

## Required recurring-workflow properties

- explicit `timeout-minutes`;
- `workflow_dispatch` recovery path;
- top-level `concurrency` with `cancel-in-progress: false` unless a task has a documented reason otherwise;
- writes limited to the owning task or explicitly registered repository-wide maintenance boundary;
- safe reruns/idempotency where the operation permits it.

For reliability-sensitive workflows, multiple cron entries may intentionally target the same concurrency group. Once one run is executing, later scheduled opportunities should act as fallbacks rather than parallel writers. Keep the behavior documented in the owning task README.

## Temporary workflows

One-shot backfill, repair, migration, probe, or diagnostic workflows may exist briefly but must never receive a recurring schedule. Remove them after successful validation.

The durable `.github/workflows/temp-work-cleanup.yml` workflow is not a disposable probe: it is the registered repository-wide lifecycle manager for `temp-work/`, owned by `temp-work/README.md` and guarded by the integrity checker.

## Public repository and Actions

This is a public repository. Useful Actions execution is not treated as scarce private-runner budget. Agents may use Actions aggressively when they materially improve reproduction, testing, validation, collection reliability, or temporary experiments.

Public visibility is the hard boundary. Treat workflow definitions, logs, Step Summaries, artifacts, cache contents, generated files, issue/PR output, and commit history as potentially public. Never expose credentials, private data, private repository/service contents, signed or credential-bearing URLs, sensitive environment dumps, or secret-derived material. Credentials belong in GitHub Actions secrets and must not be echoed or persisted.

## Avoiding waste

- Do not add scheduled repository-wide CI when an event-driven check is sufficient.
- Do not trigger validation on ordinary data snapshots unless the validation is specifically about that data.
- Use shallow/sparse checkout when practical, but prefer API-only maintenance when checkout adds no value.
- Avoid long `sleep` in Actions when the source can instead be retried in a bounded task-local collector.
- A documented warm-runner workflow is the explicit exception: when scheduler dispatch itself is the reliability risk, holding an already-acquired runner across a known publication boundary is useful work rather than waste.
- Public Actions are available to use, not a reason to create redundant jobs with no reliability, validation, or maintenance benefit.
