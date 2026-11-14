# AGENTS.md — git-mirror

`git-mirror` is the persistent task for one-shot mirrors of public Git repositories and the owner-facing `books/` shelf.

## Scope

- Use this task when the repository owner provides a public Git repository URL and wants it preserved in `web-ingest`.
- Use `git-mirror/books/` when the owner wants a book file preserved for later reading/use. Read `books/README.md` and `books/AGENTS.md` before adding one.
- The default operation is a **single mirror**, not recurring synchronization.
- Work directly on `main` unless the owner explicitly says otherwise.
- Normal imports enter through fixed Release `git-mirror-live` and persistent `.github/workflows/git-mirror-reconcile.yml`.
- Durable implementation stays under `git-mirror/`; per-repository temporary workflows are recovery tooling only.

## Source boundary

- Accept public HTTPS Git URLs only unless the owner explicitly approves a special case later.
- Never place credentials in a Git URL or mirror private repositories/private service contents.
- Do not run code from the source repository. Cloning/copying files and downloading public release assets are the operation.
- Do not initialize submodules or fetch Git LFS objects by default.
- Book files follow the separate redistribution/source rules in `books/AGENTS.md`; do not feed books through the Git repository importer.

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

The Release control plane updates exactly one concise row in `git-mirror/README.md` under **Mirrored repositories** after a successful new import, with:

- repository name;
- original upstream description;
- upstream source link;
- local **Mirror** link pointing to the mirror root.

Keep machine metadata out of the README. For GitHub, use the repository name and description returned by the upstream GitHub API verbatim apart from Markdown escaping/whitespace normalization; never invent a description. Non-GitHub sources use `—` when no deterministic metadata adapter exists. The mirror-root link is intentional: a person can open `snapshot/` for source files or `release/` for the latest release from one place.

Books maintain their own separate human index in `git-mirror/books/README.md`; do not mix books into the repository table.

## Release control plane

Normal Git repository imports:

- accept one or more public HTTPS repository URLs from the Queue block in fixed Release `git-mirror-live`;
- normalize `.git`, trailing `/`, ordinary whitespace and NBSP variants before deduplication;
- reject credential-bearing/private GitHub sources;
- process batch members independently so one bad URL does not discard other valid mirrors;
- keep existing destinations immutable and report `already mirrored` instead of refreshing them;
- run task tests and snapshot validation before committing;
- stage mirror output with `git add -f git-mirror/data` so nested upstream `.gitignore` rules cannot silently omit tracked files;
- update the human README index automatically only for newly created mirrors;
- consume the Release Queue and write per-item status back only after repository changes have been validated and pushed.

`workflow_dispatch` is the recovery entry point and must read the same fixed Release. Release-triggered runs must explicitly checkout `main` because a Release event otherwise refers to the Release tag.

The retained `render_workflow.py` / `templates/one-shot-workflow.yml.tpl` path is recovery-only. If used, keep it unscheduled, self-cleaning, validated, and isolated exactly as before.

Book imports may use a one-shot `temp-book-<slug>.yml` workflow when binary download is needed; follow `books/AGENTS.md` rather than the repository template.

## Destination layout

Git repositories:

```text
git-mirror/data/<host>/<source-path>/
├── source.json
├── snapshot/
└── release/        # optional; latest supported release only
```

Books:

```text
git-mirror/books/<book-slug>/
├── README.md
├── source.json
└── files/
```

Do not place mirrored repositories at the repository root, under `tools/`, under `books/`, or under another ingestion task. Do not place books under `data/`.

## Public repository safety

Everything copied here becomes public through `web-ingest`. If a supposedly public source contains obvious credentials, private keys, session material, personal/private data, or other material that should not be republished, stop instead of committing it.

Source `.github/workflows/` files remain nested under `snapshot/` and must never be promoted into this repository's root `.github/workflows/`. The only durable Git-mirror workflow is our own `git-mirror-reconcile.yml`; recovery one-shot workflows, when explicitly needed, come only from the retained local template.
