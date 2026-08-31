# AGENTS.md

This repository is a small Internet data-ingestion workspace. Keep it boring, explicit, and easy to inspect.

## Purpose

Use GitHub Actions or small task-local scripts to collect public Internet data and save it in this repository.

Do **not** turn this repository into the downstream analysis, reporting, archive, or email system.

## Navigation

Persistent collection tasks live directly at the repository root.

When you need to inspect, run, repair, or extend a task:

1. Read the root `README.md` to find the task.
2. Open `<task-name>/README.md` before changing anything.
3. Read `.github/workflows/<task-name>.yml` and the task-local scripts/config referenced by that README.
4. Keep changes scoped to that task unless a repository-wide rule truly needs to change.
5. If behavior changes, update the task README in the same change so the next Agent can continue from documented state.

For repository-wide scheduling, workflow policy, audits, or maintenance helpers, use `tools/` as the manager workspace. Read `tools/README.md`, `tools/AGENTS.md`, and `tools/OPERATIONS.md` before changing repository-wide behavior.

Do not invent a `tasks/` wrapper. One root-level task folder = one independent collection task.

## Task layout

Prefer this simple shape:

```text
<task-name>/
├── README.md
├── <task-specific scripts/config when needed>
└── data/
    └── YYYY/MM/DD/

.github/workflows/<task-name>.yml
```

Repository-wide maintenance tools and operational notes belong under `tools/`; do not move task implementation there.

Transient Action working files belong in the runner workspace or runner temporary directory. Do not commit temporary downloads, caches, checkpoints, or scratch files unless they are intentional task output.

## Collection rules

- One task must not depend on another task's internal files.
- Preserve source data as raw or minimally normalized data when practical.
- Store recurring snapshots under `<task-name>/data/YYYY/MM/DD/`.
- Do not silently overwrite historical snapshots.
- Re-running the same date should be safe and predictable.
- Prefer stable APIs, feeds, or documented endpoints over brittle browser scraping when both are available.
- Keep workflows small and task-specific.
- Scheduled tasks should also have a practical manual/backfill path when the source supports it.
- A successful workflow is not enough if expected output was not actually written; validate the task's documented output condition.

## Action scheduling and load

Recurring ingestion jobs in this repository are deliberately staggered rather than all starting together.

Before adding or changing any `schedule:` trigger:

1. Read `.github/workflows/README.md` and `.github/workflows/AGENTS.md`.
2. Give the workflow explicit `timeout-minutes`, `workflow_dispatch`, and top-level `concurrency`.
3. Run `python tools/check-repository-integrity.py --show`.
4. Choose a cron that does not overlap another recurring workflow's declared timeout window plus the repository planning buffer.
5. Prefer non-round minutes when practical rather than clustering jobs at `:00`.

Do not weaken the schedule guard just to accommodate a preferred time. Move the job unless there is a documented repository-level reason to change policy.

Event-driven lightweight CI is not treated as persistent ingestion load, but it must remain short and path-scoped so normal data commits do not waste Actions.

## Adding a task

For a new ingestion job:

1. Create `<task-name>/README.md` at the repository root.
2. Put task-specific code/config in that folder.
3. Put the workflow at `.github/workflows/<task-name>.yml` if automation is needed.
4. Add the task to the root README table.
5. Document source, schedule, output path/format, retry/backfill behavior, and any important failure conditions.
6. If it is scheduled, include it in the repository load plan by satisfying the schedule guard rather than manually maintaining a separate registry.

## Temporary and historical operations

- Backfills, migrations, repairs, probes, and diagnostics may use temporary workflows when Actions execution is useful.
- Temporary workflows must not have a recurring schedule.
- Remove them after successful output validation.
- Keep reusable conversion/repair logic in the task directory; the workflow itself should remain disposable.

## Public-repository safety

Never commit:

- API tokens or passwords
- cookies or session data
- private headers
- signed or expiring URLs
- personal/private source data
- secrets copied from Action logs

Use GitHub Actions secrets when a task genuinely needs credentials.

## Changes

Before changing an existing task, read its README and current workflow/script first. Avoid unrelated cleanup. If an important external decision is not documented and cannot be safely inferred from the task itself, ask rather than inventing it.

For repository-wide decisions that future Agents should remember, update durable rules in README/AGENTS or record a concise current-state note in `tools/OPERATIONS.md`. Do not leave important decisions only in chat history.
