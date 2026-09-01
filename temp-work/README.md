# Temporary Agent Workspaces

`temp-work/` is the disposable workspace for Agent experiments, investigations, validation, one-shot maintenance, and short-lived collaboration that do not belong inside an existing persistent ingestion task.

## Use

- Create one first-level directory per piece of temporary work: `temp-work/<work-name>/`.
- Use `lowercase-kebab-case` names such as `source-probe`, `issue-123-debug`, or `schedule-test`.
- Keep scripts, notes, intermediate results, and temporary outputs inside that workspace. Do not write work products directly into `temp-work/` itself and do not modify another workspace.
- Every workspace must contain a short non-empty `README.md` describing its purpose, important inputs/outputs, current conclusion, and whether anything should move into a persistent task or repository maintenance area.
- `temp-work/` is not a second persistent task namespace. Durable collection code/data belongs in the relevant root task; durable repository-wide maintenance belongs in `tools/`.

## Public-repository safety

This repository is public. Treat everything committed here, printed in Actions logs, uploaded as an artifact, or written to a Step Summary as potentially visible to anyone.

Never place secrets, tokens, passwords, cookies, sessions, private headers, private source data, personal data, private repository contents, signed/temporary URLs, or sensitive diagnostic output in `temp-work/`.

GitHub Actions may be used freely when they materially help an experiment or validation, but public visibility is the hard boundary. Use Actions secrets for credentials and make sure workflows do not echo them or persist secret-derived material.

## Lifecycle

A weekly GitHub Actions cleanup checks every first-level workspace. The activity timestamp is the most recent Git commit that touched that workspace. Workspaces untouched for more than one month are deleted automatically.

The cleanup keeps this root `README.md` and `AGENTS.md`, records its result in the Action Step Summary, and does not maintain a parallel status file.

Do not keep a workspace alive with empty edits, `touch`, or meaningless commits. If the work remains active, normal meaningful commits refresh its activity time. If the result becomes durable, migrate the useful result to its proper long-term location and let the temporary workspace disappear.

Detailed Agent boundaries are in [`AGENTS.md`](AGENTS.md).
