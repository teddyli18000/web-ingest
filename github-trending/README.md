# GitHub Trending Archive

A lightweight daily history of **GitHub Trending repositories**.

GitHub Trending is great for seeing what is hot now, but GitHub does not provide a convenient first-party way to browse the exact ranking from an arbitrary past day. This task preserves the parts that are historically useful: **rank/order, repository, language, daily-star velocity when available, and source provenance**.

It does **not** mirror repository contents, README files, screenshots, avatars, or other large assets.

<!-- archive-dashboard:start -->

### Archive at a glance

| First recovered day | Latest day | Days archived | All-Languages days |
| --- | --- | ---: | ---: |
| **2026-09-01** | **2026-09-01** | **1** | **1** |

### Latest All-Languages snapshot — 2026-09-01

| # | Repository | Language | Stars today |
| ---: | --- | --- | ---: |
| 1 | [THU-MAIC/OpenMAIC](https://github.com/THU-MAIC/OpenMAIC) | TypeScript | 2,819 |
| 2 | [tt-a1i/archify](https://github.com/tt-a1i/archify) | JavaScript | 3,993 |
| 3 | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | Python | 1,968 |
| 4 | [k1tbyte/Wand-Enhancer](https://github.com/k1tbyte/Wand-Enhancer) | C# | 511 |
| 5 | [majd/ipatool](https://github.com/majd/ipatool) | Go | 376 |
| 6 | [jingyaogong/minimind](https://github.com/jingyaogong/minimind) | Python | 472 |
| 7 | [Osmantic/ODS](https://github.com/Osmantic/ODS) | Python | 163 |
| 8 | [checkstyle/checkstyle](https://github.com/checkstyle/checkstyle) | Java | 199 |
| 9 | [zhaoxuya520/reverse-skill](https://github.com/zhaoxuya520/reverse-skill) | PowerShell | 1,439 |
| 10 | [sponsors/affaan-m](https://github.com/sponsors/affaan-m) | JavaScript | 548 |

[Open full snapshot →](data/2026/09/01/trending.json)

### Browse by year

[`2026`](data/2026/) · 1 days

<!-- archive-dashboard:end -->

## Source

Primary daily source:

- `https://github.com/trending?since=daily`

If the direct page is temporarily unavailable, the collector may use a verified same-day entry from `antonkomarev/github-trending-archive` as a fallback. The fallback is recorded in the stored snapshot rather than being presented as a direct GitHub capture.

## Schedule

Workflow: `.github/workflows/github-trending.yml`

The workflow gets three morning opportunities at **08:17, 09:17, and 10:17 Singapore/Beijing time**. The first successful snapshot for the date wins; later runs validate the existing file and exit without rewriting it. Multiple slots are intentional protection against transient GitHub/network failures.

The workflow can also be run manually.

## Output

Canonical daily data:

```text
github-trending/data/YYYY/MM/DD/trending.json
```

Schema v1 example:

```json
{
  "schema_version": 1,
  "date": "2026-09-01",
  "captured_at": "2026-09-01T08:17:08+08:00",
  "snapshots": [
    {
      "scope": "all",
      "source": "https://github.com/trending?since=daily",
      "items": [
        {
          "rank": 1,
          "repo": "owner/repo",
          "language": "Python",
          "stars_today": 967,
          "total_stars": 3938
        }
      ]
    }
  ]
}
```

Historical files can contain several scopes (`all`, `python`, `go`, etc.) when old archives preserved separate language pages. A per-language archive is **never** merged into a synthetic All-Languages ranking.

Missing historical values remain missing; the backfill does not invent `stars_today`, total stars, language, or any other field that the source did not preserve.

## Historical backfill

`github-trending/backfill.py` converts multiple public GitHub Trending archives into the same schema. The current source set is deliberately redundant so one archive can fill another's gaps:

| Source | Role |
| --- | --- |
| `larsbijl/trending_archive` | Earliest verified history; material reaches **2014-08-09**, mainly per-language lists |
| `hanishrao/trending-collection` | Additional historical gap filling |
| `ifyour/github-trending-archive` | All-Languages daily JSON from 2018-07 onward until that archive stopped |
| `Leko/github-trending-archive` | Richer per-language CSV snapshots, including historical star velocity where preserved |
| `antonkomarev/github-trending-archive` | Compact recent All-Languages and language archives |

When two sources cover the same `date + scope`, a deterministic source priority selects one canonical snapshot. Lower-priority sources only fill gaps. The actual result is summarized in `backfill-manifest.json` after the one-time backfill.

The temporary workflow `.github/workflows/github-trending-backfill.yml` exists only to perform the initial full recovery. **After a successful verified backfill it must be deleted.** Future repairs should use the task-local script manually or through a deliberately temporary workflow.

## Validation and reruns

- Existing valid daily data is append-only by default.
- Re-running the same day is a no-op.
- `--force` exists for explicit repairs; it must not be used casually against historical data.
- Every saved snapshot is schema-checked for contiguous ranks and duplicate repositories.
- The README dashboard is rebuilt from the files already stored in `data/`.

## Files

- `archive_lib.py` — schema, validation, normalization, HTML/Markdown parsers.
- `capture.py` — direct daily GitHub Trending collector.
- `backfill.py` — historical multi-source converter.
- `render_readme.py` — updates the archive dashboard above.
- `tests/` — deterministic parser/converter tests.
