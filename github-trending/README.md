# GitHub Trending Archive

A lightweight daily history of **GitHub Trending repositories**.

GitHub Trending is great for seeing what is hot now, but GitHub does not provide a convenient first-party way to browse the exact ranking from an arbitrary past day. This task preserves the parts that are historically useful: **rank/order, repository, language, daily-star velocity when available, and source provenance**.

It does **not** mirror repository contents, README files, screenshots, avatars, or other large assets.

<!-- archive-dashboard:start -->

### Archive at a glance

| First recovered day | Latest day | Days archived | All-Languages days |
| --- | --- | ---: | ---: |
| **2014-08-09** | **2026-09-01** | **4,346** | **2,499** |

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
| 10 | [affaan-m/ECC](https://github.com/affaan-m/ECC) | JavaScript | 548 |

[Open full snapshot →](data/2026/09/01/trending.json)

### Browse by year

[`2026`](data/2026/) · 244 days  
[`2025`](data/2025/) · 365 days  
[`2024`](data/2024/) · 366 days  
[`2023`](data/2023/) · 365 days  
[`2022`](data/2022/) · 365 days  
[`2021`](data/2021/) · 365 days  
[`2020`](data/2020/) · 366 days  
[`2019`](data/2019/) · 364 days  
[`2018`](data/2018/) · 365 days  
[`2017`](data/2017/) · 364 days  
[`2016`](data/2016/) · 340 days  
[`2015`](data/2015/) · 343 days  
[`2014`](data/2014/) · 134 days

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

Historical files can contain several scopes (`all`, `python`, `go`, `c++`, `c#`, etc.) when old archives preserved separate language pages. A per-language archive is **never** merged into a synthetic All-Languages ranking.

Scope names are normalized only where the mapping is unambiguous. Percent-encoded slugs are decoded and known source aliases such as `cpp` → `c++` are canonicalized. The original source and `source_path` remain in each snapshot, so the raw upstream naming can still be traced. Unknown scope names are normalized generically but are not guessed into another language.

Missing historical values remain missing; the backfill does not invent `stars_today`, total stars, language, or any other field that the source did not preserve.

## Historical backfill

`github-trending/backfill.py` is the low-level multi-source converter. Deliberate future rebuilds should enter through **`github-trending/canonical_backfill.py`**, which canonicalizes source-specific scope aliases before any files or manifest are written.

The source set is deliberately redundant so one archive can fill another's gaps:

| Source | Role |
| --- | --- |
| `larsbijl/trending_archive` | Earliest verified history; material reaches **2014-08-09**, mainly per-language lists |
| `hanishrao/trending-collection` | Additional historical gap filling |
| `ifyour/github-trending-archive` | All-Languages daily JSON from 2018-07 onward until that archive stopped |
| `Leko/github-trending-archive` | Richer per-language CSV snapshots, including historical star velocity where preserved |
| `antonkomarev/github-trending-archive` | Compact recent All-Languages and language archives |

When two sources cover the same canonical `date + scope`, a deterministic source priority selects one snapshot. Lower-priority sources only fill gaps. The actual result is summarized in `backfill-manifest.json`.

The initial full recovery completed on **2026-09-01**: **4,345 historical dates** were recovered through 2026-08-31, including **2,498 All-Languages dates** beginning 2018-07-01. Combined with the live 2026-09-01 capture, the archive currently begins at 2014-08-09 and continues through today.

The one-time full backfill workflow was removed after successful verification. Historical format repairs use task-local scripts and, only when GitHub Actions execution is useful, a temporary self-cleaning workflow that must disappear after the repair succeeds.

## Validation and reruns

- Existing valid daily data is append-only by default.
- Re-running the same day is a no-op.
- `--force` exists for explicit repairs; it must not be used casually against historical data.
- Every saved snapshot is schema-checked for contiguous ranks and duplicate repositories.
- The README dashboard is rebuilt from the files already stored in `data/`.
- Historical repairs stop at the backfill manifest's `latest_date`; they do not rewrite newer direct daily captures.

## Files

- `archive_lib.py` — schema, validation, HTML/Markdown parsers, and daily path helpers.
- `capture.py` — direct daily GitHub Trending collector.
- `backfill.py` — low-level historical multi-source converter.
- `canonical_backfill.py` — canonical entry point for future historical rebuilds.
- `scope_normalization.py` — stable scope aliases and source priority rules.
- `repair_scopes.py` — one-shot in-place canonicalization for already recovered history.
- `render_readme.py` — updates the archive dashboard above.
- `tests/` — deterministic parser/converter/normalization tests.
