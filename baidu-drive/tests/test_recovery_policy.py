from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import relay_state
import scheduler
import lease_heartbeat

UTC=dt.timezone.utc


def record(now):
    return relay_state.new_record("task-1",{
        "file_id":"file-1","batch_id":"batch-1","logical_path":"/a",
        "parent_path":"/","name":"a","size":10,"md5":"",
        "baidu_staging_path":"/BaiduDriveMover/test/a","drive_parent_id":"folder",
    },now)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.now=dt.datetime(2026,11,14,15,tzinfo=UTC)

    def test_legacy_lease_is_not_reclaimed_during_live_512mib_upload(self):
        active=record(self.now)
        active.update(status="ACTIVE",lease_id="old",lease_heartbeat_protocol=0,
                      heartbeat_at=relay_state.now_iso(self.now))
        self.assertTrue(scheduler.is_active(active,self.now+dt.timedelta(hours=2)))
        self.assertFalse(relay_state.runnable(active,self.now+dt.timedelta(hours=2)))
        self.assertTrue(relay_state.runnable(active,self.now+dt.timedelta(hours=7)))

    def test_monitored_lease_can_renew_and_expire(self):
        active=relay_state.claim(record(self.now),"lease",self.now)
        self.assertEqual(active["lease_heartbeat_protocol"],2)
        at=self.now+dt.timedelta(minutes=30)
        fresh=relay_state.renew_lease(active,"lease",at)
        self.assertFalse(relay_state.runnable(fresh,at+dt.timedelta(minutes=40)))
        self.assertTrue(relay_state.runnable(fresh,at+dt.timedelta(minutes=50)))
        with self.assertRaises(relay_state.RelayStateError):
            relay_state.renew_lease(fresh,"wrong",at)

    def test_infinite_retry_waits_for_due_date_and_preserves_checkpoint(self):
        active=relay_state.claim(record(self.now),"lease",self.now)
        active=relay_state.apply_relay_checkpoint(active,"lease",5,5,"hashstate",None,self.now)
        with mock.patch("relay_state.secrets.randbelow",return_value=17):
            failed=relay_state.fail(active,"lease",self.now,"provider unavailable")
        self.assertEqual(failed["next_retry_at"],relay_state.now_iso(self.now+dt.timedelta(seconds=47)))
        self.assertEqual(failed["confirmed_offset"],5)
        self.assertFalse(scheduler.is_runnable(failed,self.now))
        self.assertTrue(scheduler.is_runnable(failed,self.now+dt.timedelta(minutes=1)))
        self.assertTrue(relay_state.runnable(failed,self.now+dt.timedelta(minutes=1)))
        failed["retryable_failures"]=1000
        self.assertTrue(scheduler.is_runnable(failed,self.now+dt.timedelta(hours=1)))

    def test_heartbeat_verifies_ownership(self):
        repo=mock.Mock()
        active=relay_state.claim(record(self.now),"lease",self.now)
        repo.read_record.return_value=(active,"sha")
        repo.mutate_record.side_effect=lambda task,file,fn,msg: fn(active)
        self.assertTrue(lease_heartbeat.renew_once(repo,"task-1","file-1","lease"))
        repo.read_record.return_value=({**active,"lease_id":"replacement"},"sha")
        self.assertFalse(lease_heartbeat.renew_once(repo,"task-1","file-1","lease"))


if __name__=="__main__":
    unittest.main()
