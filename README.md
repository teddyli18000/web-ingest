# web-ingest

A simple GitHub Actions workspace for collecting public Internet data on a schedule.

The repository only handles **collection and storage**. Downstream analysis, archiving, reporting, or delivery belongs elsewhere.

## Structure

```text
web-ingest/
├── README.md
├── AGENTS.md
└── tasks/
    ├── README.md
    └── <task-name>/
        ├── README.md
        └── data/
            └── YYYY/MM/DD/
```

When a task needs automation, its workflow lives at:

```text
.github/workflows/<task-name>.yml
```

Task-specific scripts and configuration stay inside that task's folder rather than in a shared framework.

## Tasks

| Task | Purpose | Status |
| --- | --- | --- |
| [`ai-daily`](tasks/ai-daily/) | Mirror the daily AIHOT report | Active — daily 08:17 Beijing time |

## Conventions

- One folder = one independent collection task.
- Recurring snapshots use `data/YYYY/MM/DD/`.
- Keep raw or minimally normalized source data whenever practical.
- Historical data should be append-only; do not silently rewrite old snapshots.
- A completed collection may include a small `manifest.json` describing the run and its files.
- Keep the repository simple. Do not introduce shared infrastructure until multiple tasks genuinely need it.
- This is a public repository: never commit tokens, cookies, credentials, signed URLs, or other secrets.
