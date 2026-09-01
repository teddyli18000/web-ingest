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

For temporary experiments, investigations, validation, one-shot maintenance, and short-lived collaboration that do not belong to an existing persistent task, use `temp-work/<work-name>/`. Read `temp-work/README.md` and `temp-work/AGENTS.md` first. Do not scatter temporary files across the repository or use another task directory as scratch space.

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

Transient Action working files belong in the runner workspace or runner temporary directory. Committed short-lived Agent work belongs under `temp-work/<work-name>/`, not at the repository root or inside a persistent task.

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

This is a public repository. Actions runner time is not treated as the same scarce resource as in a private repository, so Agents may use Actions aggressively when they materially improve reproduction, testing, validation, collection reliability, or temporary experiments. Do not create waste for its own sake, but do not avoid a useful Action merely to save public-repository minutes.

## Adding a task

For a new ingestion job:

1. Create `<task-name>/README.md` at the repository root.
2. Put task-specific code/config in that folder.
3. Put the workflow at `.github/workflows/<task-name>.yml` if automation is needed.
4. Add the task to the root README table.
5. Document source, schedule, output path/format, retry/backfill behavior, and any important failure conditions.
6. If it is scheduled, include it in the repository load plan by satisfying the schedule guard rather than manually maintaining a separate registry.

## Temporary Agent work

- If work is not clearly part of an existing persistent task, create `temp-work/<work-name>/` using `lowercase-kebab-case`.
- One first-level workspace = one temporary task. Do not modify another workspace.
- Every workspace must have a short non-empty `README.md` recording purpose, important context, outputs/conclusions, and whether anything should migrate into durable repository state.
- `temp-work/` is disposable. `.github/workflows/temp-work-cleanup.yml` removes first-level workspaces with no meaningful commit for more than one month.
- Do not keep temporary work alive with empty edits, file touching, or meaningless commits.
- When an experiment produces a durable result, migrate only the validated long-term change into the appropriate task or `tools/`; do not let `temp-work/` become a second permanent task hierarchy.

## Temporary and historical operations

- Backfills, migrations, repairs, probes, and diagnostics may use temporary workflows when Actions execution is useful.
- Temporary workflows must not have a recurring schedule. The durable repository-wide `temp-work-cleanup.yml` lifecycle workflow is the explicit exception and is registered by the integrity checker.
- Remove disposable workflows after successful output validation.
- Keep reusable conversion/repair logic in the task directory; the workflow itself should remain disposable.

## Public-repository safety

Everything committed here or emitted by Actions should be treated as potentially public, including Git history, logs, Step Summaries, artifacts, issue/PR discussion, and diagnostic output.

Never commit or expose:

- API tokens, keys, passwords, or credentials
- cookies or session data
- private headers
- signed, expiring, credential-bearing, or otherwise sensitive URLs
- personal/private source data
- private repository or private service contents
- secrets copied from Action logs
- diagnostic dumps containing credentials, user data, or private environment information

Use GitHub Actions secrets when a task genuinely needs credentials, and make sure workflows do not echo secrets or persist secret-derived material into files, logs, summaries, or artifacts.

## Changes

Before changing an existing task, read its README and current workflow/script first. Avoid unrelated cleanup. If an important external decision is not documented and cannot be safely inferred from the task itself, ask rather than inventing it.

For repository-wide decisions that future Agents should remember, update durable rules in README/AGENTS or record a concise current-state note in `tools/OPERATIONS.md`. Do not leave important decisions only in chat history.
