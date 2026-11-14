# Public Git Repository Mirror

`git-mirror` stores **one-shot mirrors** of public Git repositories for later use, plus a small human-facing [`books/`](books/) shelf for book files the owner wants preserved alongside those mirrors.

The normal control surface is the fixed **Git Mirror** Release (`git-mirror-live`). Paste one public repository URL per line into its **Queue** and update the Release; the persistent Action normalizes the URL, mirrors the repository, captures the latest formal GitHub Release when available, validates the result, updates this index, commits to `main`, and writes the result back to the same Release.

This task is still **one-shot per source**, not a synchronization service. Existing mirrors are reported but never overwritten or refreshed automatically.

## Fixed Release

Normal use requires no temporary workflow and no Agent intervention:

1. Open the fixed Release [`git-mirror-live`](https://github.com/teddyli18000/web-ingest/releases/tag/git-mirror-live).
2. Paste one public HTTPS Git repository URL per line between the Queue markers.
3. Choose **Update release**.
4. `Git Mirror Reconcile` processes every queued line, commits successful mirrors, clears the queue, and writes per-item results back under **Last result**.

Both `https://github.com/example/project.git` and `https://github.com/example/project` are accepted, as are trailing `/`, normal whitespace, and non-breaking spaces. Duplicate URLs in the same batch are ignored. GitHub repository name and description are taken directly from the upstream GitHub API; no generated description is invented. For non-GitHub Git hosts, the description is `—` unless a later host-specific metadata adapter is added.

`workflow_dispatch` reprocesses the current fixed Release and is the recovery path. The retained one-shot workflow renderer remains only as a maintenance fallback.

## Mirrored repositories

<!-- mirror-index:start -->

| Repository | Description | Source | Mirror |
| --- | --- | --- | --- |
| ARTEX | AI 自主渗透测试系统 \| 百度“agent+”攻防挑战赛冠军项目 | [mhtsec/ARTEX](https://github.com/mhtsec/ARTEX) | [Mirror](data/github.com/mhtsec/ARTEX/) |
| dsh-infinite-gen-5 | DeepSeek v4.1 flash 逆向工具（无限五代） | [Minglink/dsh-infinite-gen-5](https://github.com/Minglink/dsh-infinite-gen-5) | [Mirror](data/github.com/Minglink/dsh-infinite-gen-5/) |
| SDAutoLogin | Soochow Wi-Fi /Ethernet keeps ghosting you? This auto network guard & login buddy has your back. | [zqlan/SDAutoLogin](https://git.zqlhub.com/zqlan/SDAutoLogin) | [Mirror](data/git.zqlhub.com/zqlan/SDAutoLogin/) |

<!-- mirror-index:end -->

Keep this table for people: one concise row per mirrored repository. Detailed provenance belongs inside that mirror, not here.

## Books

[`books/`](books/) is the durable bookshelf for readable book files. It has its own short human index and one directory per edition/translation, with the actual PDF/EPUB files plus source provenance.

Keep Git repository mirrors under `data/` and books under `books/`; do not mix the two layouts.

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
- `release_control.py` — owns fixed-Release parsing, URL normalization, batch processing, upstream GitHub metadata, README index updates, and Release status projection.
- `.github/workflows/git-mirror-reconcile.yml` — persistent Release/event entry point; explicitly checks out `main` before processing.
- `render_workflow.py` / `templates/one-shot-workflow.yml.tpl` — retained recovery tooling for a manually isolated one-shot import, not the normal control path.
- `validate_snapshots.py` — validates stored mirrors.
- `tests/` — deterministic task tests; they do not contact external repositories.
- `books/` — human-facing bookshelf with its own local README and Agent rules.

## Agent procedure

For normal Git repository imports, do not create a per-repository workflow. Use the fixed `git-mirror-live` Release exactly as the owner does. The control plane performs URL normalization, public-source checks, metadata lookup, import, release capture, validation, README indexing, commit, and status projection automatically.

Use `render_workflow.py` and the retained one-shot template only when the fixed Release path itself is being repaired or a deliberately isolated recovery import is required.

For books, read `books/README.md` and `books/AGENTS.md` instead of using the Git repository importer.

## Safety

- Treat source repositories as public input, not trusted executable code.
- Do not run source build scripts, hooks, package installers, tests, or arbitrary commands.
- Never import a private repository or credential-bearing URL.
- Do not follow submodules or LFS objects automatically.
- Do not rewrite source files merely for style.
- Source `.github/workflows/` files stay nested inside `snapshot/`; they are data, not workflows for `web-ingest`.

## Updates

There is deliberately no normal update/sync behavior. If the owner later requests another snapshot of an already mirrored repository, handle that case explicitly at the time.
