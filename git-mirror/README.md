# Public Git Repository Mirror

`git-mirror` stores **one-shot mirrors** of public Git repositories for later use.

The repository owner supplies a public repository URL. An Agent creates a temporary GitHub Actions workflow from the retained template, the Action shallow-clones the requested source branch, captures the latest formal release when supported, commits the mirror to `main`, and removes the temporary workflow.

This task is **not** a synchronization service. There is no recurring schedule and no automatic refresh policy.

## Mirrored repositories

| Repository | Description | Source | Mirror |
| --- | --- | --- | --- |
| ARTEX | AI 自主渗透测试系统 \| 百度“agent+”攻防挑战赛冠军项目 | [mhtsec/ARTEX](https://github.com/mhtsec/ARTEX) | [Mirror](data/github.com/mhtsec/ARTEX/) |

Keep this table for people: one concise row per mirrored repository. Detailed provenance belongs inside that mirror, not here.

## What is preserved

For a source such as:

```text
https://github.com/example/project.git
```

the default destination is:

```text
git-mirror/data/github.com/example/project/
├── source.json
├── snapshot/
│   └── <source repository working tree>
└── release/                 # only when a supported latest release exists
    ├── README.md             # title, tag, date, source link, full release notes
    ├── release.json          # machine-readable release metadata
    └── assets/               # mirrored uploaded release attachments
```

The snapshot contains the checked-out files only. It intentionally does **not** contain the source repository's `.git` history.

For GitHub repositories, the importer also captures the **latest formal Release** when one exists. Release notes are preserved in full, and uploaded release assets are mirrored subject to the same repository-safety size limits. GitHub-generated source archives are not duplicated because `snapshot/` already preserves the source files.

## Source policy

- Public **HTTPS Git URLs only** by default.
- GitHub, GitLab, Codeberg, Gitea, and other publicly cloneable HTTPS Git hosts can be mirrored as repository snapshots.
- If no branch is specified, Git chooses the source repository's default branch.
- Cloning is shallow (`--depth 1 --single-branch`).
- Git LFS smudging is disabled: LFS pointer files are preserved instead of automatically downloading large LFS objects.
- Submodules are **not initialized or recursively cloned**. Their gitlink commit IDs are recorded in `source.json`; `.gitmodules`, when present, remains part of the file snapshot.
- Symlinks are preserved as symlinks rather than followed.
- Existing mirror destinations are not overwritten. A second import requires an explicit later decision by the repository owner.
- Release capture is currently implemented for GitHub. Other hosts keep the repository snapshot; add host-specific release support only when a real source requires it.

## Size guard

The importer defaults to:

- maximum individual regular file or release asset: **90 MiB**;
- maximum snapshot payload: **500 MiB**;
- maximum mirrored release assets in total: **500 MiB**.

Assets over the limit are not downloaded; their upstream name/link remains in `release.json` and the human-readable release README.

## Durable files

- `import_snapshot.py` — shallow-clones the source, builds the working-tree snapshot, and writes provenance.
- `collect_latest_release.py` — captures the latest formal GitHub release, full release notes, and eligible uploaded assets.
- `render_workflow.py` — renders the retained one-shot workflow template for a concrete source URL.
- `templates/one-shot-workflow.yml.tpl` — template copied into `.github/workflows/` only for one import.
- `validate_snapshots.py` — validates stored mirrors.
- `tests/` — deterministic task tests; they do not contact external repositories.

## Agent procedure

1. Read this README and `AGENTS.md`.
2. Take the public repository URL supplied by the owner. Use the source default branch unless another branch is specified.
3. Look up the upstream repository name and original description for the human-facing asset table.
4. Render and commit a temporary one-shot workflow to `main`.
5. The Action validates this task, imports `snapshot/`, captures the latest supported release, validates the result, removes its own workflow, and pushes the mirror to `main`.
6. Verify the resulting mirror, then add one row to **Mirrored repositories** using the upstream repository name and original description. Link **Mirror** to the local mirror root so `snapshot/` and `release/` are both easy to reach.

## Safety

- Treat source repositories as public input, not trusted executable code.
- Do not run source build scripts, hooks, package installers, tests, or arbitrary commands.
- Never import a private repository or credential-bearing URL.
- Do not follow submodules or LFS objects automatically.
- Do not rewrite source files merely for style.
- Source `.github/workflows/` files stay nested inside `snapshot/`; they are data, not workflows for `web-ingest`.

## Updates

There is deliberately no normal update/sync behavior. If the owner later requests another snapshot of an already mirrored repository, handle that case explicitly at the time.
