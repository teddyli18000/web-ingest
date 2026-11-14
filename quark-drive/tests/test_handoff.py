from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import relay_state
import scheduler

UTC = dt.timezone.utc


def initial(now):
    return relay_state.new_record("qk-task",{
        "file_id":"file-1","batch_id":"batch-1",
        "logical_path":"/movie.mp4","parent_path":"/",
        "name":"movie.mp4","size":100,"md5":"",
        "quark_fid":"saved-fid","drive_parent_id":"google-root",
    },now)


class QuarkHandoffTests(unittest.TestCase):
    def setUp(self):
        self.now=dt.datetime(2026,11,14,18,0,tzinfo=UTC)

    def test_lease_takeover_preserves_drive_checkpoint_and_fences_old_worker(self):
        owned=relay_state.claim(initial(self.now),"lease-one",self.now)
        owned=relay_state.apply_relay_checkpoint(owned,"lease-one",25,25,"stream-hash",None,self.now)
        alive=relay_state.renew_lease(owned,"lease-one",self.now+dt.timedelta(minutes=30))
        with self.assertRaises(relay_state.RelayStateError):
            relay_state.claim(alive,"lease-two",self.now+dt.timedelta(minutes=50))
        restarted=relay_state.claim(alive,"lease-two",self.now+dt.timedelta(minutes=76))
        self.assertEqual(restarted["confirmed_offset"],25)
        self.assertEqual(restarted["hash_offset"],25)
        self.assertEqual(restarted["md5_state"],"stream-hash")
        with self.assertRaises(relay_state.RelayStateError):
            relay_state.apply_relay_checkpoint(restarted,"lease-one",50,50,"other",None,self.now)

    def test_provider_failure_retries_after_jitter_without_loss(self):
        owned=relay_state.claim(initial(self.now),"lease-one",self.now)
        owned=relay_state.apply_relay_checkpoint(owned,"lease-one",30,30,"hash",None,self.now)
        with mock.patch("relay_state.secrets.randbelow",return_value=3):
            failed=relay_state.fail(owned,"lease-one",self.now,"Quark CDN unavailable",permanent=False)
        self.assertEqual(failed["status"],relay_state.FAILED_RETRYABLE)
        self.assertEqual(failed["confirmed_offset"],30)
        self.assertEqual(failed["next_retry_at"],relay_state.now_iso(self.now+dt.timedelta(seconds=33)))
        self.assertEqual(scheduler.choose_files([failed],self.now),[])
        self.assertEqual(scheduler.choose_files([failed],self.now+dt.timedelta(minutes=1)),["file-1"])


if __name__=="__main__":
    unittest.main()
