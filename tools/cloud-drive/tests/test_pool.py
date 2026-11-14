from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pool import Provider, allocate, live, demand, ready

UTC = dt.timezone.utc


class PoolTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 11, 14, 16, 0, tzinfo=UTC)

    def file(self, status, *, age=0, size=100, version=2, retry_at=None):
        return {"status": status, "size": size, "confirmed_offset": 0,
                "lease_heartbeat_protocol": version, "heartbeat_at": (self.now - dt.timedelta(minutes=age)).isoformat(),
                "next_retry_at": retry_at}

    def provider(self, name, *files):
        return Provider(name, "task", "RUNNING", list(files))

    def test_single_provider_uses_all_three_slots(self):
        self.assertEqual(allocate([Provider("baidu", "task", "RUNNING", [self.file("READY")], files_total=3)], self.now), {"baidu": 3})

    def test_baidu_quark_share_one_global_pool(self):
        b = self.provider("baidu", self.file("ACTIVE", age=5), self.file("READY"))
        q = self.provider("quark", self.file("READY"))
        result = allocate([b,q], self.now)
        self.assertEqual(sum(result.values()), 2)
        self.assertEqual(result, {"baidu": 1, "quark": 1})

    def test_global_capacity_never_exceeds_three(self):
        b = self.provider("baidu", self.file("ACTIVE"), self.file("ACTIVE"), self.file("READY"))
        q = self.provider("quark", self.file("ACTIVE"), self.file("READY"))
        self.assertEqual(allocate([b,q], self.now), {"baidu": 0, "quark": 0})

    def test_old_and_monitored_lease_recovery(self):
        self.assertTrue(live(self.file("ACTIVE", age=120, version=0), self.now))
        self.assertFalse(live(self.file("ACTIVE", age=50, version=2), self.now))

    def test_jitter_retry_respects_due_time(self):
        target=(self.now+dt.timedelta(hours=1)).isoformat()
        p=self.provider("baidu", self.file("FAILED_RETRYABLE", retry_at=target))
        self.assertFalse(demand(p,self.now))
        self.assertTrue(demand(p,self.now+dt.timedelta(hours=2)))


    def test_unstaged_files_count_toward_provider_demand(self):
        b = Provider("baidu", "task", "RUNNING", [self.file("ACTIVE")], files_total=8)
        self.assertEqual(allocate([b], self.now), {"baidu": 2})

    def test_all_verified_triggers_final_cleanup(self):
        b = self.provider("baidu", self.file("VERIFIED"))
        self.assertEqual(allocate([b], self.now), {"baidu": 1})


class FakeGitHub:
    def __init__(self, now):
        self.now = now
        self.dispatched = []
        self.write_calls = 0
        self.state = None
        self.running_preparations = set()
        self.tasks = {
            "baidu": {"id": "task-b", "status": "RUNNING", "files_total": 8, "bytes_done": 0},
            "quark": {"id": "task-q", "status": "RUNNING", "files_total": 1, "bytes_done": 0},
        }
        self.records = {
            "baidu": [{"status": "READY", "size": 1000, "confirmed_offset": 0}],
            "quark": [{"status": "READY", "size": 100, "confirmed_offset": 0}],
        }

    def read(self, path):
        if path == "tools/cloud-drive/state/supervisor.json":
            return self.state, "sha"
        for provider, task in self.tasks.items():
            if path == f"{provider}-drive/state/runtime.json":
                return {"active_task": task["id"]}, "sha"
            if path == f"{provider}-drive/state/tasks/{task['id']}.json":
                return task, "sha"
            if path.startswith(f"{provider}-drive/state/files/"):
                return self.records[provider][0], "sha"
        return None, None

    def directory(self, path):
        for provider, task in self.tasks.items():
            if path == f"{provider}-drive/state/files/{task['id']}":
                return [path + "/first.json"]
        return []

    def write(self, path, value, sha):
        self.write_calls += 1
        self.state = value

    def preparation_is_running(self, provider, issued_at):
        return provider in self.running_preparations

    def dispatch(self, provider, task_id, capacity, reason="shared-supervisor"):
        self.dispatched.append((provider, task_id, capacity))


class SupervisorTests(unittest.TestCase):
    def test_queued_reservations_prevent_duplicate_dispatch(self):
        from supervisor import run
        now = dt.datetime(2026, 11, 14, 16, tzinfo=UTC)
        gh = FakeGitHub(now)
        result = run(gh, now)
        self.assertEqual(result, {"baidu": 2, "quark": 1})
        self.assertEqual(gh.dispatched, [("baidu", "task-b", 2), ("quark", "task-q", 1)])
        self.assertEqual(gh.write_calls, 1)
        self.assertEqual(run(gh, now + dt.timedelta(minutes=1)), {"baidu": 0, "quark": 0})
        self.assertEqual(len(gh.dispatched), 2)

    def test_queued_prepare_still_owns_slots_after_twelve_minutes(self):
        from supervisor import run
        now = dt.datetime(2026, 11, 14, 16, tzinfo=UTC)
        gh = FakeGitHub(now)
        gh.running_preparations = {"baidu", "quark"}
        run(gh, now)
        result = run(gh, now + dt.timedelta(minutes=15))
        self.assertEqual(result, {"baidu": 0, "quark": 0})
        self.assertEqual(len(gh.dispatched), 2)

    def test_lost_prepare_dispatch_released_after_grace(self):
        from supervisor import run
        now = dt.datetime(2026, 11, 14, 16, tzinfo=UTC)
        gh = FakeGitHub(now)
        run(gh, now)
        result = run(gh, now + dt.timedelta(minutes=15))
        self.assertEqual(result, {"baidu": 2, "quark": 1})
        self.assertEqual(len(gh.dispatched), 4)

if __name__ == "__main__":
    unittest.main()
