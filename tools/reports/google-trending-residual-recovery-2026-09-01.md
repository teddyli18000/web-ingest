# Google Trending residual recovery — 2026-09-01

## Recovered

- **2025-02-05:** recovered **GB, SG, US** from `connorodea/Google-Trends-Keywords-Scraper` commit `ce3c2897587e504e2934535795498f93e805d342`.
- The source collector at that commit directly used Google's legacy Hot Trends Atom endpoint. Region IDs were SG=`p5`, US=`p1`, GB=`p9`.
- Source feed order, item titles, published timestamps and Google links were preserved. Search-volume fields remain `null` where the old snapshot did not preserve them.
- Existing HK data from `googletrendarchive` was not replaced.

## Unresolved source-side gaps

- **2025-03-24:** SG / US / GB / HK remain unavailable.
- **2025-03-27:** HK remains unavailable.

The primary GitHub RSS mirror had no source commit for those UTC dates. The following long-lived forks were also checked and had no commit on the unresolved dates:

- `connorodea/Google-Trends-Keywords-Scraper`
- `DutchErwin/Google-Trends-Keywords-Scraper`
- `mapledxf/Google-Trends-Keywords-Scraper`
- `253611069/Google-Trends-Keywords-Scraper`
- `langtuandroid/Google-Trends-Keywords-Scraper`
- `mupsje/Google-Trends-Keywords-Scraper`
- `dennyhaq/Google-Trends-Keywords-Scraper`
- `CattleZoe/Google-Trends-Keywords-Scraper`
- `VisionDirectingStudio/Google-Trends-Keywords-Scraper`
- `pixelapps-dev/Google-Trends-Keywords-Scraper`
- `danteGPT/Google-Trends-Keywords-Scraper`
- `e5dmnyKSA/Google-Trends-Keywords-Scraper`

Because these repositories share the same scraper lineage and all show the same date-level outage, no later 48-hour snapshot is backdated or synthesized as a missing daily snapshot.

## 2026 required gap

The required **2026-01-04 through 2026-08-31** mirror range remains complete for SG / US / GB / HK.
