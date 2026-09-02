# AGENTS.md — temp-work

This directory is a disposable Agent workspace, not persistent storage.

## Write boundary

- Temporary work lives under `temp-work/<work-name>/`.
- `<work-name>` uses `lowercase-kebab-case`; one first-level directory represents one temporary task.
- Do not write work products directly into `temp-work/`; its root is repository-managed.
- Do not modify another first-level workspace.
- Do not use a temporary workspace as an excuse to modify `ai-daily/`, `github-trending/`, `google-trending/`, `tools/`, repository root files, or persistent workflows unless the current user task explicitly requires that durable change.
- When an experiment proves a durable change is needed, keep the experiment isolated first, validate it, then make the smallest intentional change in the proper persistent location.

## Work directly on main

Temporary Agents normally work directly on `main`. Do not create a branch or PR just for ordinary `temp-work/` activity.

Keep repository coordination out of the Agent's way:

- Do not perform a separate `main` HEAD check, branch synchronization ritual, or repository-wide preflight before every write.
- Prefer creating task-specific files instead of repeatedly rewriting shared status files. Independent files naturally allow several Agents to work at once.
- If an existing file must be changed, read that file itself and use the current blob SHA required by GitHub's file-update API. No separate HEAD read is required.
- If an update is rejected because that exact file changed concurrently, re-read only that file, preserve the other writer's work, and retry the smallest intended edit. Do not force-push, reset, rewrite history, or revert another Agent's work to make a write succeed.
- Commit only meaningful work. Repository-wide coordination, lifecycle cleanup, and workspace patrol belong to repository maintenance.

## Minimum record

Every `temp-work/<work-name>/` must contain a non-empty `README.md` that briefly records:

- the problem or experiment;
- important context or inputs;
- significant outputs or conclusions;
- whether any result should be migrated into a persistent task or repository-wide maintenance area.

The README establishes the workspace; Agents do not need to rewrite it on every small step. Prefer notes, experiments, and result files for active work when that reduces contention.

Do not create elaborate status systems, dashboards, or metadata just for temporary work.

## Public-repository safety

This repository is public. Assume committed files, Git history, Actions logs, Step Summaries, artifacts, issue/PR discussion, and workflow output can be publicly visible.

Never commit or expose:

- tokens, passwords, API keys, cookies, sessions, private headers, or credentials;
- private or personal source data;
- content copied from private repositories or private services;
- signed, temporary, credential-bearing, or otherwise sensitive URLs;
- secrets or sensitive values copied from Actions logs;
- diagnostic dumps that contain credentials, user data, or private environment information.

Actions are not scarce here and may be used aggressively when useful for testing, reproduction, validation, or short-lived automation. That freedom does not relax the public-data boundary. Credentials must use GitHub Actions secrets and workflows must not echo or archive them.

## Repository-managed patrol

- `.github/workflows/temp-work-patrol.yml` is a lightweight patrol for direct-to-main temporary work.
- It records boundary incidents such as one commit touching multiple temporary workspaces or temporary work spilling outside its workspace.
- High commit frequency is normal and is intentionally ignored.
- Recorded incidents are written to the workflow Step Summary for later inspection; an incident does not fail or block the Agent's work.
- `.github/workflows/temp-work-cleanup.yml` handles workspace lifecycle cleanup.

## Lifecycle

- `.github/workflows/temp-work-cleanup.yml` checks first-level workspaces weekly.
- Activity is the latest Git commit timestamp touching the workspace.
- A workspace untouched for more than one month is deleted automatically without a preservation guarantee.
- Cleanup does not remove repository-managed files at the `temp-work/` root.
- Do not evade cleanup with empty changes, file touching, or meaningless commits.

## Promotion to durable work

If temporary work needs to become a persistent collector or repository-level maintenance feature, move only the validated durable result into the appropriate existing task, a user-approved new root task, or `tools/`. Do not turn `temp-work/` into a permanent parallel structure.
