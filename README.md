# web-ingest

A simple GitHub Actions workspace for collecting public Internet data on a schedule.

The repository only handles **collection and storage**. Downstream analysis, archiving, reporting, or delivery belongs elsewhere.

## Structure

Each persistent collection task lives directly at the repository root. Repository-wide maintenance utilities live separately in `tools/`.

```text
web-ingest/
├── README.md
├── AGENTS.md
├── .github/
│   └── workflows/
│       ├── <task-name>.yml
│       └── repository-integrity.yml
├── tools/
│   ├── README.md
│   ├── AGENTS.md
│   ├── OPERATIONS.md
│   └── <repository maintenance tools>
├── ai-daily/
│   ├── README.md
│   ├── <task-specific scripts/config>
│   └── data/
│       └── YYYY/MM/DD/
└── <another-task>/
    ├── README.md
    └── data/
```

There is intentionally no shared `tasks/` namespace. One root-level task folder = one independent Internet collection job. `tools/` is not a task wrapper; it is the repository manager workspace for cross-task maintenance, schedule validation, audits, and operational notes.

Transient Action working files should stay in the runner workspace or runner temporary directory and should not become part of the persistent repository structure.

## Tasks

| Task | Purpose | Status |
| --- | --- | --- |
| [`ai-daily`](ai-daily/) | Byte-mirror the AIHOT daily webpage and REST API v1 response | Active |
| [`github-trending`](github-trending/) | Preserve daily GitHub Trending rankings and recover available historical snapshots | Active |
| [`google-trending`](google-trending/) | Preserve Google Trends Trending Now for Singapore and the United States, with historical recovery where available | Active |

## Repository management

- [`tools/`](tools/) contains repository-wide maintenance helpers and operational state.
- [`tools/check-repository-integrity.py`](tools/check-repository-integrity.py) validates recurring Action scheduling and core maintenance rules.
- [`.github/workflows/README.md`](.github/workflows/README.md) documents the current load plan and workflow policy.

## Conventions

- One root-level task folder = one independent collection task.
- Every task folder must contain a `README.md` that explains source, schedule, workflow, output, and maintenance/recovery behavior.
- Task workflows live in `.github/workflows/<task-name>.yml` because GitHub requires workflows there.
- Task-specific scripts and configuration stay inside the task folder.
- Repository-wide maintenance code and notes belong in `tools/`.
- Recurring snapshots use `<task-name>/data/YYYY/MM/DD/`.
- Keep raw or minimally normalized source data whenever practical.
- Historical data should be append-only; do not silently rewrite old snapshots.
- Scheduled collection jobs must be load-balanced rather than clustered; the repository guard checks declared timeouts plus a buffer.
- Keep the repository simple. Shared maintenance infrastructure is allowed when it manages the repository as a whole; shared task/business frameworks still require a real multi-task need.
- This is a public repository: never commit tokens, cookies, credentials, signed URLs, or other secrets.

For Agent navigation and modification rules, read [`AGENTS.md`](AGENTS.md).
