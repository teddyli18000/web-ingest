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


if __name__ == "__main__":
    unittest.main()
