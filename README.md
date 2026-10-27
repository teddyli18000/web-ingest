# web-ingest

A simple GitHub Actions workspace for collecting and preserving public Internet data through scheduled or one-shot jobs.

Most of the repository handles **collection and storage**. Downstream analysis, archiving, reporting, or delivery belongs elsewhere. The explicit exception is [`science-boundary/`](science-boundary/), a durable multi-Agent workspace for scientific frontier exploration.

## Structure

Each persistent collection task lives directly at the repository root. Repository-wide maintenance utilities live separately in `tools/`, short-lived Agent experiments and investigations go under `temp-work/`, and durable frontier research lives under `science-boundary/`.

```text
web-ingest/
├── README.md
├── AGENTS.md
├── .github/
│   └── workflows/
│       ├── <task-name>.yml
│       ├── repository-integrity.yml
│       └── temp-work-cleanup.yml
├── tools/
│   ├── README.md
│   ├── AGENTS.md
│   ├── OPERATIONS.md
│   └── <repository maintenance tools>
├── temp-work/
│   ├── README.md
│   ├── AGENTS.md
│   └── <work-name>/
│       └── README.md
├── science-boundary/
│   ├── README.md
│   ├── AGENTS.md
│   └── <research-topic>/
│       └── README.md
├── ai-daily/
│   ├── README.md
│   ├── <task-specific scripts/config>
│   └── data/
│       └── YYYY/MM/DD/
└── <another-task>/
    ├── README.md
    └── data/
```

There is intentionally no shared `tasks/` namespace. One root-level task folder = one independent Internet collection job. `tools/` is not a task wrapper; it is the repository manager workspace for cross-task maintenance, schedule validation, audits, and operational notes. `temp-work/` is a disposable workspace for Agent experiments, probes, investigations, and one-shot collaboration; it is not a persistent task namespace. `science-boundary/` is the deliberate long-term exception for cumulative scientific research across many Agents.

Transient Action working files should stay in the runner workspace or runner temporary directory unless the experiment intentionally needs a short-lived committed workspace under `temp-work/` or produces a durable scientific artifact owned by a `science-boundary/` topic.

## Tasks

| Task | Purpose | Status |
| --- | --- | --- |
| [`ai-daily`](ai-daily/) | Byte-mirror the AIHOT daily webpage and REST API v1 response | Active |
| [`github-trending`](github-trending/) | Preserve daily GitHub Trending rankings and recover available historical snapshots | Active |
| [`google-trending`](google-trending/) | Preserve Google Trends Trending Now for Singapore, the United States, the United Kingdom, and Hong Kong, with historical recovery where available | Active |
| [`git-mirror`](git-mirror/) | Import one-shot file snapshots of public Git repositories through temporary self-cleaning Actions | Ready |
| [`baidu-drive`](baidu-drive/) | Release-controlled transfer of public Baidu Netdisk shares to Google Drive | Control, scheduler, relay, and recovery ready; auth/live acceptance pending |

## Research workspace

[`science-boundary/`](science-boundary/) is a permanent, human-readable multi-Agent workspace for exploring questions near the current boundaries of human scientific knowledge. Independent directions live directly under `science-boundary/<research-topic>/`; each topic keeps its own durable handoff, evidence, experiments, dead ends, and useful reproducible artifacts.

It is not subject to `temp-work/` cleanup.

## Repository management

- [`tools/`](tools/) contains repository-wide maintenance helpers and operational state.
- [`temp-work/`](temp-work/) is the disposable Agent workspace. Each `temp-work/<work-name>/` is isolated and is automatically eligible for deletion after one month without a meaningful commit.
- [`science-boundary/`](science-boundary/) contains durable scientific frontier research and its multi-Agent handoff rules.
- [`tools/check-repository-integrity.py`](tools/check-repository-integrity.py) validates recurring Action scheduling and core maintenance rules.
- [`.github/workflows/README.md`](.github/workflows/README.md) documents the current load plan and workflow policy.

## Conventions

- One root-level task folder = one independent collection task, except the explicitly registered repository workspaces `tools/`, `temp-work/`, and `science-boundary/`.
- Every task folder must contain a `README.md` that explains source, schedule/workflow behavior, output, and maintenance/recovery behavior.
- Task workflows live in `.github/workflows/<task-name>.yml` when durable automation is needed because GitHub requires workflows there. One-shot tasks may instead create a temporary self-cleaning workflow from a retained task-local template.
- Task-specific scripts and configuration stay inside the task folder.
- Repository-wide maintenance code and notes belong in `tools/`.
- Temporary Agent work belongs in `temp-work/<work-name>/`, never at the `temp-work/` root or inside an unrelated persistent task.
- Durable scientific frontier work belongs in `science-boundary/<research-topic>/` and follows `science-boundary/AGENTS.md`.
- Recurring snapshots use `<task-name>/data/YYYY/MM/DD/` unless a task README explicitly documents a source-keyed one-shot layout instead.
- Keep raw or minimally normalized source data whenever practical.
- Historical data should be append-only; do not silently rewrite old snapshots.
- Scheduled collection jobs must be load-balanced rather than clustered; the repository guard checks declared timeouts plus a buffer.
- Keep the repository simple. Shared maintenance infrastructure is allowed when it manages the repository as a whole; shared task/business/research frameworks still require a real repeated need.

## Public repository safety

This repository is public. GitHub Actions can be used aggressively when they materially improve testing, reproduction, validation, collection reliability, short-lived Agent work, or scientific computation; runner minutes are not treated as the same scarce resource as in a private repository.

The tradeoff is visibility: assume committed files, Git history, Actions logs, Step Summaries, artifacts, issue/PR discussion, and workflow output may be visible to anyone.

Never commit or expose tokens, passwords, API keys, cookies, sessions, credentials, private headers, personal/private source data, private repository contents, signed or temporary credential-bearing URLs, secrets copied from Actions logs, restricted/non-public research material, or sensitive diagnostic dumps. Use GitHub Actions secrets when credentials are genuinely required, and do not echo or archive sensitive derived material.

For Agent navigation and modification rules, read [`AGENTS.md`](AGENTS.md).
