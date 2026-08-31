# AI Daily

Collection workspace for the source data used by the AI daily report.

## Status

Scaffold only. Sources, APIs, collection schedule, and workflow are intentionally not defined yet.

## Output

Recurring data should be stored under:

```text
data/YYYY/MM/DD/
```

A completed daily snapshot may include `manifest.json` plus the collected source files for that day.

Keep this task limited to collection and storage. Downstream summarization, archiving, and delivery are outside this repository.
