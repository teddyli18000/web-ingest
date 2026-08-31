# Repository Tools

`tools/` contains only maintenance code that applies to the whole `web-ingest` repository.

## Current tool

### `check-repository-integrity.py`

Validates repository-wide maintenance rules and the scheduled GitHub Actions load plan.

It checks that:

- required repository/workflow maintenance documentation exists;
- every scheduled workflow has `workflow_dispatch`, top-level `concurrency`, and `timeout-minutes`;
- every scheduled task has a matching root task `README.md`;
- temporary migration/backfill/repair/probe workflows are not scheduled;
- supported cron expressions can be parsed;
- scheduled workflows do not overlap another workflow's worst-case `timeout-minutes` window plus a 15-minute cross-workflow buffer.

Run locally with:

```bash
python tools/check-repository-integrity.py
```

Show the current schedule plan with:

```bash
python tools/check-repository-integrity.py --show
```

The same tool is run by `.github/workflows/repository-integrity.yml` when repository rules, workflows, or maintenance tools change. It is intentionally **not** a scheduled Action.

## Design rule

Task-specific collectors, converters, parsers, or repair scripts belong in their task directory. Put something in `tools/` only when it protects or manages the repository as a whole.
