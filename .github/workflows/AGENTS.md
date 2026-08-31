# AGENTS.md — workflows

Workflow files are thin orchestration layers. Keep collection/conversion logic in the corresponding task directory and repository-wide validation logic in `tools/`.

## Before changing a recurring workflow

1. Read the task README and current workflow.
2. Read `tools/README.md` and the workflow operations README in this directory.
3. Run or reason against `tools/check-repository-integrity.py --show` before choosing a cron.
4. Preserve load balance: do not overlap another recurring workflow's declared timeout window plus repository buffer.
5. Update task documentation when the schedule or behavior changes.

## Required recurring-workflow properties

- explicit `timeout-minutes`;
- `workflow_dispatch` recovery path;
- top-level `concurrency` with `cancel-in-progress: false` unless a task has a documented reason otherwise;
- task-local writes only;
- safe same-day reruns/idempotency where the source permits it.

## Temporary workflows

One-shot backfill, repair, migration, probe, or diagnostic workflows may exist briefly but must never receive a recurring schedule. Remove them after successful validation.

## Avoiding waste

- Do not add scheduled repository-wide CI when an event-driven check is sufficient.
- Do not trigger validation on ordinary data snapshots unless the validation is specifically about that data.
- Use shallow/sparse checkout when practical.
- Avoid long `sleep` in Actions when the source can instead be retried in a bounded task-local collector.
