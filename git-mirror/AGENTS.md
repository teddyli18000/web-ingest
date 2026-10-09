# AGENTS.md — git-mirror

`git-mirror` is the persistent task for one-shot mirrors of public Git repositories.

## Scope

- Use this task when the repository owner provides a public Git repository URL and wants it preserved in `web-ingest`.
- The default operation is a **single mirror**, not recurring synchronization.
- Work directly on `main` unless the owner explicitly says otherwise.
- Durable implementation stays under `git-mirror/`; each import workflow is temporary under `.github/workflows/`.

## Source boundary

- Accept public HTTPS Git URLs only unless the owner explicitly approves a special case later.
- Never place credentials in a Git URL or mirror private repositories/private service contents.
- Do not run code from the source repository. Cloning/copying files and downloading public release assets are the operation.
- Do not initialize submodules or fetch Git LFS objects by default.

## Mirror behavior

- Use a shallow single-branch clone and the source default branch unless another branch is specified.
- Preserve the checked-out working tree under `snapshot/`, excluding source `.git` metadata.
- Preserve symlinks without following them.
- Record exact source provenance in `source.json`.
- Fail if the destination already exists. Do not invent merge/update semantics.
- Respect file and total-size guards unless the owner explicitly decides otherwise for a particular source.
- For GitHub sources, capture only the **latest formal Release** when one exists: preserve the complete release notes, metadata, and eligible uploaded assets under `release/`.
- Do not duplicate GitHub-generated source zip/tar archives; `snapshot/` already contains the source tree.
- For non-GitHub hosts, keep the repository snapshot. Add release support for another host only when a concrete source requires it; do not add speculative adapters.

## Human-facing asset index

After a successful import, add exactly one concise row to `git-mirror/README.md` under **Mirrored repositories** with:

- repository name;
- original upstream description;
- upstream source link;
- local **Mirror** link pointing to the mirror root.

Keep machine metadata out of the README. The mirror-root link is intentional: a person can open `snapshot/` for source files or `release/` for the latest release from one place.

## Temporary workflow

- Start from `templates/one-shot-workflow.yml.tpl` or `render_workflow.py`.
- No recurring `schedule:` trigger.
- Prefer a path-scoped `push` trigger on the workflow file plus `workflow_dispatch` for recovery.
- Give the job an explicit timeout and unique concurrency group.
- Run `git-mirror` tests before importing.
- Stage only the mirror output and the temporary workflow's own deletion.
- Stage mirror output with `git add -f git-mirror/data`. A source repository may intentionally track files that match its own nested `.gitignore`; ordinary `git add` in `web-ingest` would otherwise silently omit them.
- Rebase on latest `main` before pushing.
- Remove the temporary workflow after a successful validated import.

## Destination layout

```text
git-mirror/data/<host>/<source-path>/
├── source.json
├── snapshot/
└── release/        # optional; latest supported release only
```

Do not place mirrored repositories at the repository root, under `tools/`, or under another ingestion task.

## Public repository safety

Everything copied here becomes public through `web-ingest`. If a supposedly public source contains obvious credentials, private keys, session material, personal/private data, or other material that should not be republished, stop instead of committing it.

Source `.github/workflows/` files remain nested under `snapshot/` and must never be promoted into this repository's root `.github/workflows/` except for the temporary importer workflow created from our own retained template.
