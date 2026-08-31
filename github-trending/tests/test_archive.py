import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archive_lib import day_path, parse_markdown_language_archive, parse_trending_html, validate_day
from backfill import import_ifyour, import_leko


class ArchiveTests(unittest.TestCase):
    def test_trending_html(self):
        html = '''
        <article class="Box-row">
          <a href="/sponsors/owner">Sponsor</a>
          <h2><a href="/owner/repo"> owner / repo </a></h2>
          <span itemprop="programmingLanguage">Python</span>
          <a href="/owner/repo/stargazers">3,938</a>
          <a href="/owner/repo/forks">472</a>
          <span class="d-inline-block float-sm-right">967 stars today</span>
        </article>
        <article class="Box-row">
          <h2><a href="/other/tool"> other / tool </a></h2>
          <span itemprop="programmingLanguage">Rust</span>
          <a href="/other/tool/stargazers">12,345</a>
          <span class="d-inline-block float-sm-right">21 stars today</span>
        </article>
        '''
        items = parse_trending_html(html)
        self.assertEqual(items[0], {"rank": 1, "repo": "owner/repo", "language": "Python",
                                    "stars_today": 967, "total_stars": 3938, "forks": 472})
        self.assertEqual(items[1]["repo"], "other/tool")

    def test_markdown_archive(self):
        text = '''###2014-08-09\n\n####python\n* [pybee/toga](https://github.com/pybee/toga): x\n* [django/django](https://github.com/django/django): y\n\n####go\n* [g/u](https://github.com/g/u): z\n'''
        scopes = parse_markdown_language_archive(text)
        self.assertEqual([x["repo"] for x in scopes["python"]], ["pybee/toga", "django/django"])
        self.assertEqual(scopes["go"][0]["rank"], 1)

    def test_ifyour_is_real_all_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "data" / "2018-07-01.json").write_text(json.dumps([
                {"title": "a/b", "lang": "Python"}, {"title": "c/d", "lang": "Go"}
            ]), encoding="utf-8")
            store = {}
            import_ifyour(store, root, 360)
            self.assertIn("all", store["2018-07-01"])

    def test_leko_rich_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            day = root / "archive" / "raw" / "2022-01-01"
            day.mkdir(parents=True)
            with (day / "python.csv").open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["date", "language", "stargazers", "starsToday", "description", "owner", "name", "url"])
                w.writerow(["2022-01-01", "Python", "7700", "88", "x", "lucidrains", "vit-pytorch", "https://github.com/lucidrains/vit-pytorch"])
            store = {}
            import_leko(store, root, 420)
            entry = store["2022-01-01"]["python"][1]["items"][0]
            self.assertEqual(entry["stars_today"], 88)
            self.assertEqual(entry["total_stars"], 7700)

    def test_day_path_and_validation(self):
        path = day_path(Path("github-trending"), "2026-09-01")
        self.assertEqual(path.as_posix(), "github-trending/data/2026/09/01/trending.json")
        validate_day({"schema_version": 1, "date": "2026-09-01", "captured_at": None,
                      "snapshots": [{"scope": "all", "source": "x", "items": [{"rank": 1, "repo": "a/b"}]}]})


if __name__ == "__main__":
    unittest.main()
