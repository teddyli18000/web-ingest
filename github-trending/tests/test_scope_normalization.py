import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backfill import merge
from repair_scopes import canonicalize_day, normalization_summary
from scope_normalization import normalize_scope


class ScopeNormalizationTests(unittest.TestCase):
    def test_unambiguous_aliases(self):
        self.assertEqual(normalize_scope("cpp"), "c++")
        self.assertEqual(normalize_scope("C++"), "c++")
        self.assertEqual(normalize_scope("c%23"), "c#")
        self.assertEqual(normalize_scope("C#"), "c#")
        self.assertEqual(normalize_scope("Objective C"), "objective-c")

    def test_collision_keeps_higher_priority_source(self):
        day = {
            "schema_version": 1,
            "date": "2022-01-01",
            "captured_at": None,
            "snapshots": [
                {
                    "scope": "cpp",
                    "source": "larsbijl/trending_archive",
                    "source_path": "old.md",
                    "items": [{"rank": 1, "repo": "old/source"}],
                },
                {
                    "scope": "c++",
                    "source": "Leko/github-trending-archive",
                    "source_path": "new.csv",
                    "items": [{"rank": 1, "repo": "better/source"}],
                },
            ],
        }
        repaired, renamed, collisions = canonicalize_day(day)
        self.assertEqual(renamed, 1)
        self.assertEqual(collisions, 1)
        self.assertEqual(len(repaired["snapshots"]), 1)
        self.assertEqual(repaired["snapshots"][0]["scope"], "c++")
        self.assertEqual(repaired["snapshots"][0]["items"][0]["repo"], "better/source")

    def test_backfill_merges_aliases_under_one_canonical_key(self):
        store = {}
        low = {
            "scope": "cpp",
            "source": "larsbijl/trending_archive",
            "source_path": "old.md",
            "items": [{"rank": 1, "repo": "old/source"}],
        }
        high = {
            "scope": "c++",
            "source": "Leko/github-trending-archive",
            "source_path": "new.csv",
            "items": [{"rank": 1, "repo": "better/source"}],
        }
        self.assertTrue(merge(store, "2022-01-01", "cpp", 220, low))
        self.assertTrue(merge(store, "2022-01-01", "c++", 420, high))
        self.assertEqual(set(store["2022-01-01"]), {"c++"})
        self.assertEqual(store["2022-01-01"]["c++"][1]["items"][0]["repo"], "better/source")

    def test_normalization_stats_survive_noop_rerun(self):
        manifest = {
            "scope_normalization": {
                "renamed_snapshots_seen": 4146,
                "alias_collisions_resolved": 1063,
                "files_changed": 4145,
            }
        }
        summary = normalization_summary(manifest, 0, 0, 0)
        self.assertEqual(summary["renamed_snapshots_seen"], 4146)
        self.assertEqual(summary["alias_collisions_resolved"], 1063)
        self.assertEqual(summary["files_changed"], 4145)

    def test_normalization_stats_accumulate_future_repairs(self):
        manifest = {
            "scope_normalization": {
                "renamed_snapshots_seen": 10,
                "alias_collisions_resolved": 3,
                "files_changed": 8,
            }
        }
        summary = normalization_summary(manifest, 2, 1, 2)
        self.assertEqual(summary["renamed_snapshots_seen"], 12)
        self.assertEqual(summary["alias_collisions_resolved"], 4)
        self.assertEqual(summary["files_changed"], 10)

    def test_unknown_scope_is_not_guessed(self):
        self.assertEqual(normalize_scope("Some New Lang"), "some-new-lang")


if __name__ == "__main__":
    unittest.main()
