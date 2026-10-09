# Public Git Repository Mirror

`git-mirror` stores **one-shot file snapshots** of public Git repositories for later use.

The normal workflow is intentionally simple: the repository owner supplies a public repository URL, an Agent creates a temporary GitHub Actions workflow from the retained template, the Action shallow-clones the requested source branch, commits a file snapshot plus provenance to `main`, and then removes the temporary workflow.

This task is **not** a synchronization service. There is no recurring schedule and no automatic refresh policy.

## Mirrored repositories

| Repository | Description | Source | Snapshot |
| --- | --- | --- | --- |
| _No repositories mirrored yet._ |  |  |  |

Keep this table for people: one concise row per mirrored repository. Detailed provenance belongs in that snapshot's `source.json`, not here.

## What is preserved

For a source such as:

```text
https://github.com/example/project.git
```

the default destination is:

```text
git-mirror/data/github.com/example/project/
├── source.json
└── snapshot/
    └── <source repository working tree>
```

`source.json` records the original URL, selected branch/ref, exact source commit and tree SHA, source commit time, import time, file/byte counts, submodule gitlinks, and the policies used during import.

The snapshot contains the checked-out files only. It intentionally does **not** contain the source repository's `.git` history.

## Source policy

- Public **HTTPS Git URLs only** by default.
- GitHub, GitLab, Codeberg, Gitea, and other publicly cloneable HTTPS Git hosts are treated the same way.
- If no branch is specified, Git chooses the source repository's default branch.
- Cloning is shallow (`--depth 1 --single-branch`).
- Git LFS smudging is disabled: LFS pointer files are preserved instead of automatically downloading large LFS objects.
- Submodules are **not initialized or recursively cloned**. Their gitlink commit IDs are recorded in `source.json`; `.gitmodules`, when present, remains part of the file snapshot.
- Symlinks are preserved as symlinks rather than followed.
- Existing mirror destinations are not overwritten. A second import of the same logical destination requires an explicit later decision by the repository owner.

## Size guard

The importer defaults to:

- maximum individual regular file: **90 MiB**;
- maximum snapshot payload: **500 MiB**.

These are repository-safety guards rather than claims about upstream repository size. An Agent may only change them for a specific import when the repository owner has a reason to do so.

## Durable files

- `import_snapshot.py` — validates the public Git URL, shallow-clones the source, builds the snapshot and writes provenance.
- `render_workflow.py` — renders the retained one-shot workflow template for a concrete source URL.
- `templates/one-shot-workflow.yml.tpl` — template copied into `.github/workflows/` only for the lifetime of one import.
- `tests/` — deterministic tests for URL/destination/template behavior; they do not contact external repositories.

## Agent procedure

1. Read this README and `AGENTS.md`.
2. Take the repository URL supplied by the owner. Use the source default branch unless the owner specifies another branch.
3. Render a temporary workflow, for example:

   ```bash
   python git-mirror/render_workflow.py \
     --source-url https://github.com/example/project.git \
     --output .github/workflows/git-mirror-example-project.yml
   ```

4. Commit the temporary workflow directly to `main`. Its path-scoped `push` trigger starts the import.
5. The Action runs the task tests, imports the snapshot, stages `git-mirror/data/`, removes its own workflow, commits the result, rebases on latest `main`, and pushes.
6. Verify the resulting `source.json` and snapshot exist, then add one row to **Mirrored repositories** using the upstream repository name and original description. No temporary workflow should remain after success.

Agents using the GitHub file API rather than a local checkout may fill `templates/one-shot-workflow.yml.tpl` directly. Keep the same behavior: one-shot, path-scoped trigger, no schedule, and self-removal after a validated import.

## Output and provenance rules

- Treat the source repository as public input, not as trusted executable code.
- Do not run build scripts, hooks, package installers, tests, or arbitrary commands from the mirrored repository.
- Never import a private repository, credential-bearing URL, cookie, session, token, or private artifact.
- Do not follow Git submodules or LFS objects automatically.
- Do not rewrite or normalize source files merely for style.
- Do not fabricate source commit metadata.
- The source repository's own `.github/workflows/` directory is safe inside the nested snapshot path; it is data and is never copied into this repository's root `.github/workflows/`.

## Updates

There is deliberately no normal update/sync behavior. If the owner later requests a second snapshot of an already mirrored repository, handle that request explicitly at that time rather than encoding a standing refresh policy now.
