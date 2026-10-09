from __future__ import annotations

import sys
import unittest
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from import_snapshot import default_destination, destination_path, validate_source_url
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
            "https://user:token@github.com/openai/openai-python.git",
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

    def test_renderer_creates_path_scoped_self_cleaning_workflow(self):
        path, content = render("https://github.com/example/project.git", branch="main")
        self.assertTrue(path.startswith(".github/workflows/git-mirror-project-"))
        self.assertIn('SOURCE_URL: "https://github.com/example/project.git"', content)
        self.assertIn('SOURCE_BRANCH: "main"', content)
        self.assertIn(f'WORKFLOW_PATH: "{path}"', content)
        self.assertIn('git rm -- "$WORKFLOW_PATH"', content)
        self.assertNotIn("schedule:", content)
        self.assertNotIn("{{", content)


if __name__ == "__main__":
    unittest.main()
