# AGENTS.md — temp-work

This directory is a disposable Agent workspace, not persistent storage.

## Write boundary

- Temporary work must live under `temp-work/<work-name>/`.
- `<work-name>` must use `lowercase-kebab-case`; one first-level directory represents one temporary task.
- Do not write work products directly into `temp-work/`; its root only contains this `AGENTS.md` and `README.md`.
- Do not modify another first-level workspace.
- Do not use a temporary workspace as an excuse to modify `ai-daily/`, `github-trending/`, `google-trending/`, `tools/`, repository root files, or persistent workflows unless the current user task explicitly requires that durable change.
- When an experiment proves a durable change is needed, keep the experiment isolated first, validate it, then make the smallest intentional change in the proper persistent location.

## Minimum record

Every `temp-work/<work-name>/` must contain a non-empty `README.md` that briefly records:

- the problem or experiment;
- important context or inputs;
- significant outputs or conclusions;
- whether any result should be migrated into a persistent task or repository-wide maintenance area.

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

## Lifecycle

- `.github/workflows/temp-work-cleanup.yml` checks first-level workspaces weekly.
- Activity is the latest Git commit timestamp touching the workspace.
- A workspace untouched for more than one month is deleted automatically without a preservation guarantee.
- Cleanup does not remove the root `README.md` or `AGENTS.md`.
- Do not evade cleanup with empty changes, file touching, or meaningless commits.

## Promotion to durable work

If temporary work needs to become a persistent collector or repository-level maintenance feature, move only the validated durable result into the appropriate existing task, a user-approved new root task, or `tools/`. Do not turn `temp-work/` into a permanent parallel structure.
