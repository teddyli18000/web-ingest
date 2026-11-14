from __future__ import annotations

import sys
import unittest
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from collect_latest_release import github_repo, safe_name
from import_snapshot import default_destination, destination_path, validate_source_url
from release_control import (
    INDEX_END,
    INDEX_START,
    QUEUE_END,
    QUEUE_START,
    SourceInfo,
    normalize_source_url,
    queue_lines,
    release_body,
    upsert_readme,
)
from render_workflow import render


class GitMirrorTests(unittest.TestCase):
    def test_public_https_url_is_allowed(self):
        self.assertEqual(
            validate_source_url("https://github.com/openai/openai-python.git"),
            "https://github.com/openai/openai-python.git",
        )

    def test_non_https_and_credentials_are_rejected(self):
        invalid = [
            "git@github.com:openai/openai-python.git",
            "ssh://git@github.com/openai/openai-python.git",
            "http://github.com/openai/openai-python.git",
            "https://user:token@github.com/openai-python.git",
            "https://localhost/example/repo.git",
            "https://127.0.0.1/example/repo.git",
        ]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_source_url(value)

    def test_default_destination_preserves_host_and_nested_path(self):
        self.assertEqual(
            default_destination("https://gitlab.com/group/subgroup/repo.git"),
            "gitlab.com/group/subgroup/repo",
        )

    def test_destination_rejects_parent_escape(self):
        with self.assertRaises(ValueError):
            destination_path("../outside")

    def test_github_release_source_detection(self):
        self.assertEqual(
            github_repo(https://github.com/example/project.git"),
            ("example", "project"),
        )
        self.assertIsNone(github_repo("https://gitlab.com/example/project.git"))

    def test_release_asset_name_cannot_escape_directory(self):
        self.assertEqual(safe_name("../../build.zip"), "build.zip")

    def test_release_url_normalization_accepts_git_slash_and_unicode_space(self):
        variants = [
            "https://github.com/example/project.git",
            "https://github.com/example/project/",
            "  https://github.com/example/project.git\u00a0",
        ]
        for value in variants:
            with self.subTest(value=value):
                self.assertEqual(normalize_source_url(value), "https://github.com/example/project")

    def test_release_url_rejects_non_repository_github_paths(self):
        with self.assertRaises(ValueError):
            normalize_source_url("https://github.com/example/project/tree/main")

    def test_release_queue_reads_one_line_per_request(self):
        body = f"""# Git Mirror
{QUEUE_START}
https://github.com/example/one.git
https://github.com/example/two
{QUEUE_END}
"""
        self.assertEqual(
            queue_lines(body),
            ["https://github.com/example/one.git", "https://github.com/example/two"],
        )

    def test_release_body_starts_with_empty_queue(self):
        body = release_body()
        self.assertIn(f"{QUEUE_START}\n\n{QUEUE_END}", body)
        self.assertIn("No requests processed yet.", body)

    def test_readme_index_upsert_is_deterministic_and_escapes_description(self):
        readme = f"""# Public Git Repository Mirror

{INDEX_START}

| Repository | Description | Source | Mirror |
| --- | --- | --- | --- |
| Zed | old | [example/zed](https://github.com/example/zed) | [Mirror](data/github.com/example/zed/) |

{INDEX_END}
"""
        info = SourceInfo(
            clone_url="https://github.com/example/alpha",
            web_url="https://github.com/example/alpha",
            repository_name="alpha",
            source_label="example/alpha",
            description="A | useful repo",
            destination="github.com/example/alpha",
        )
        updated = upsert_readme(readme, [info])
        self.assertIn("A \\| useful repo", updated)
        self.assertLess(updated.index("| alpha |"), updated.index("| Zed |"))

    def test_renderer_creates_path_scoped_self_cleaning_workflow(self):
        path, content = render("https://github.com/example/project.git", branch="main")
        self.assertTrue(path.startswith(".github/workflows/git-mirror-project-"))
        self.assertIn('SOURCE_URL: "https://github.com/example/project.git"', content)
        self.assertIn('SOURCE_BRANCH: "main"', content)
        self.assertIn(f'WORKFLOW_PATH: "{path}"', content)
        self.assertIn("collect_latest_release.py", content)
        self.assertIn("${{ github.token }}", content)
        self.assertIn("git add -f git-mirror/data", content)
        self.assertIn("git rm -- \"$WORKFLOW_PATH\"", content)
        self.assertNotIn("schedule:", content)
        for token in (
            "{{LABEL}}",
            "{{SLUG}}",
            "{{SOURCE_URL_JSON}}",
            "{{SOURCE_BRANCH_JSON}}",
            "{{DESTINATION_JSON}}",
            "{{WORKFLOW_PATH_JSON}}",
        ):
            self.assertNotIn(token, content)


if __name__ == "__main__":
    unittest.main()
