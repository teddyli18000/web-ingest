# AGENTS.md

This repository is a small Internet data-ingestion workspace. Keep it boring, explicit, and easy to inspect.

## Purpose

Use GitHub Actions or small task-local scripts to collect public Internet data and save it in this repository.

Do **not** turn this repository into the downstream analysis, reporting, archive, or email system.

## How to navigate

1. Read the root `README.md` for the task registry.
2. Open `tasks/<task-name>/README.md` before changing a task.
3. Keep all task-specific code, config, notes, and collected data under that task directory unless GitHub requires a root-level location such as `.github/workflows/`.
4. A workflow for a task should normally be named `.github/workflows/<task-name>.yml`.

## Task layout

Prefer this simple shape:

```text
tasks/<task-name>/
├── README.md
├── <task-specific scripts/config when needed>
└── data/
    └── YYYY/MM/DD/
```

Do not create extra framework directories unless they are actually needed.

## Collection rules

- One task must not depend on another task's internal files.
- Preserve source data as raw or minimally normalized data when practical.
- Store recurring snapshots by date under `data/YYYY/MM/DD/`.
- Do not silently overwrite historical snapshots.
- Re-running the same date should be safe and predictable.
- When useful, write `manifest.json` beside a completed snapshot with collection time, source summary, status, and file list.
- Prefer stable APIs, feeds, or documented endpoints over brittle browser scraping when both are available.
- Keep workflows small and task-specific.

## Public-repository safety

Never commit:

- API tokens or passwords
- cookies or session data
- private headers
- signed or expiring URLs
- personal/private source data
- secrets copied from Action logs

Use GitHub Actions secrets when a task genuinely needs credentials.

## Changes

Before changing an existing task, read its README and current workflow/script first. Avoid unrelated cleanup. If an important design choice is not already defined, ask rather than inventing it.

When adding a new task, add it to the root README task table and create `tasks/<task-name>/README.md` explaining what it collects, how often it runs, its sources, and its output format.
