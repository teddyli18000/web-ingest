from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth_notice  # noqa: E402
import controller  # noqa: E402


class FakeGH:
    api = "https://api.github.com/repos/owner/repo"

    def __init__(self):
        self.task = {"id": "bd-20261106T120000Z-abcdef", "status": "NEEDS_LOGIN"}
        self.issue = None
        self.events = []

    def read_json(self, path, default=None):
        if path == controller.RUNTIME_PATH:
            return {"active_task": self.task["id"]}, None
        return self.task, None

    def request(self, method, url, obj=None):
        if method == "GET" and "/issues?" in url:
            return [self.issue] if self.issue else []
        self.events.append((method, url, obj))
        if method == "POST" and url.endswith("/issues"):
            self.issue = {"number": 17, "title": auth_notice.TITLE, "state": "open"}
        elif method == "PATCH" and "/issues/17" in url:
            self.issue["state"] = obj["state"]
        return self.issue


class NoticeTests(unittest.TestCase):
    def test_single_issue_reused_and_closed_on_recovery(self):
        gh = FakeGH()
        auth_notice.synchronize(gh)
        self.assertEqual(len(gh.events), 1)
        self.assertIn("@teddyli18000", gh.events[0][2]["body"])
        auth_notice.synchronize(gh)
        self.assertEqual(len(gh.events), 1)

        gh.task["status"] = "RUNNING"
        auth_notice.synchronize(gh)
        self.assertEqual(gh.issue["state"], "closed")
        gh.task["status"] = "NEEDS_LOGIN"
        auth_notice.synchronize(gh)
        self.assertEqual(gh.issue["state"], "open")
        self.assertEqual(len(gh.events), 4)

    def test_closes_issue_when_active_task_is_canceled_or_completed(self):
        gh = FakeGH()
        auth_notice.synchronize(gh)
        self.assertEqual(gh.issue["state"], "open")
        original_read = gh.read_json

        def no_active(path, default=None):
            if path == controller.RUNTIME_PATH:
                return {"active_task": None, "last_task": gh.task["id"]}, None
            return original_read(path, default)

        gh.read_json = no_active
        auth_notice.synchronize(gh)
        self.assertEqual(gh.issue["state"], "closed")

    def test_never_posts_secrets_to_issue(self):
        self.assertNotIn("BDUSS=", auth_notice.BODY)
        self.assertNotIn("STOKEN=", auth_notice.BODY)


if __name__ == "__main__":
    unittest.main()
