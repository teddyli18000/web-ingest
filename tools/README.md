# Repository Tools

`tools/` is the repository manager workspace for `web-ingest`. It can contain multiple small utilities and maintenance notes when they apply to the repository as a whole.

## Current contents

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

### `OPERATIONS.md`

Compact working memory for repository-wide operating decisions, the current recurring load plan, known maintenance state, and near-term ingestion ideas that future Agents should not have to rediscover from chat history.

It should stay concise. Once an operational decision becomes a stable rule, move that rule into the appropriate README/AGENTS file and trim obsolete notes.

## Design rule

Task-specific collectors, converters, parsers, or repair scripts belong in their task directory. Put something in `tools/` when it protects, inspects, migrates, or manages the repository as a whole.

Prefer several small explicit tools over one large repository framework. Add tooling only when it removes a real maintenance burden or makes a rule executable.
