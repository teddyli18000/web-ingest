# web-ingest

A simple GitHub Actions workspace for collecting public Internet data on a schedule.

The repository only handles **collection and storage**. Downstream analysis, archiving, reporting, or delivery belongs elsewhere.

## Structure

Each persistent collection task lives directly at the repository root:

```text
web-ingest/
├── README.md
├── AGENTS.md
├── .github/
│   └── workflows/
│       └── <task-name>.yml
├── ai-daily/
│   ├── README.md
│   ├── <task-specific scripts/config>
│   └── data/
│       └── YYYY/MM/DD/
└── <another-task>/
    ├── README.md
    └── data/
```

There is intentionally no shared `tasks/` namespace. One root-level task folder = one independent Internet collection job.

Transient Action working files should stay in the runner workspace or runner temporary directory and should not become part of the persistent repository structure.

## Tasks

| Task | Purpose | Status |
| --- | --- | --- |
| [`ai-daily`](ai-daily/) | Byte-mirror the AIHOT daily webpage and REST API v1 response | Active |
| [`github-trending`](github-trending/) | Preserve daily GitHub Trending rankings and recover available historical snapshots | Active |

## Conventions

- One root-level folder = one independent collection task.
- Every task folder must contain a `README.md` that explains source, schedule, workflow, output, and maintenance/recovery behavior.
- Task workflows live in `.github/workflows/<task-name>.yml` because GitHub requires workflows there.
- Task-specific scripts and configuration stay inside the task folder.
- Recurring snapshots use `<task-name>/data/YYYY/MM/DD/`.
- Keep raw or minimally normalized source data whenever practical.
- Historical data should be append-only; do not silently rewrite old snapshots.
- Keep the repository simple. Do not introduce shared infrastructure until multiple tasks genuinely need it.
- This is a public repository: never commit tokens, cookies, credentials, signed URLs, or other secrets.

For Agent navigation and modification rules, read [`AGENTS.md`](AGENTS.md).
