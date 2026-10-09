# AGENTS.md — git-mirror

`git-mirror` is the persistent task for one-shot snapshots of public Git repositories.

## Scope

- Use this task when the repository owner provides a public Git repository URL and wants its files preserved in `web-ingest`.
- The default operation is a **single snapshot**, not recurring synchronization.
- Work directly on `main` unless the owner explicitly says otherwise.
- The durable implementation stays under `git-mirror/`; the per-import workflow is temporary and lives briefly under `.github/workflows/`.

## Source boundary

- Accept public HTTPS Git URLs only unless the owner explicitly approves a special case later.
- Never place credentials in a Git URL.
- Never mirror private repositories or private service contents.
- Do not run code from the source repository. Cloning and copying files is the operation; source build/test/install hooks are out of scope.
- Do not initialize submodules or fetch Git LFS objects by default.

## Snapshot behavior

- Use a shallow single-branch clone.
- Use the source default branch when no branch is specified.
- Preserve the checked-out working tree, excluding source `.git` metadata.
- Preserve symlinks without following them.
- Record exact source provenance in the sibling `source.json`.
- Fail if the chosen destination already exists. Do not invent merge/update semantics.
- Respect the importer's file-size and total-size guards unless the owner explicitly decides otherwise for a particular source.

## Temporary workflow

- Start from `templates/one-shot-workflow.yml.tpl` or `render_workflow.py`.
- A concrete import workflow must have no `schedule:` trigger.
- Prefer a path-scoped `push` trigger on the workflow file itself plus `workflow_dispatch` for recovery.
- Give the job an explicit timeout and a unique concurrency group.
- Run `git-mirror` tests before importing.
- Stage only the mirror output and the temporary workflow's own deletion.
- Rebase on latest `main` before pushing the resulting commit.
- Remove the temporary workflow after a successful validated import.

## Destination layout

Default layout:

```text
git-mirror/data/<host>/<source-path>/
├── source.json
└── snapshot/
```

Do not place mirrored repositories at the repository root, under `tools/`, or under another ingestion task.

## Public repository safety

Everything copied here becomes public through `web-ingest`. If a supposedly public source contains obvious credentials, private keys, session material, personal/private data, or other material that should not be republished, stop instead of committing it.

Source `.github/workflows/` files remain nested under the snapshot directory and must never be promoted into this repository's root `.github/workflows/` except for the one temporary importer workflow created from our own retained template.
