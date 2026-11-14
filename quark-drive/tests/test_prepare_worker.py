from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import api
import prepare_worker as p

class PrepTests(unittest.TestCase):
    def test_source_identity_stable_and_snapshot_has_no_share_token(self):
        f=api.ShareFile("fid-1","private-share-token","n.bin",25,"dir/n.bin")
        result=p.snapshot([f])
        self.assertEqual(result[0]["file_id"],p.source_id(f))
        self.assertNotIn("private-share-token",str(result))
        self.assertEqual(result[0]["parent_path"],"dir")

    def test_stage_adopts_existing_tool_owned_file(self):
        c=mock.Mock()
        c.list_folder.return_value=[{"fid":"saved-file","file_name":"n.bin","size":25,"dir":False}]
        f=api.ShareFile("fid-1","share-token","n.bin",25,"dir/n.bin")
        self.assertEqual(p.stage_one(c,"share","token",f,"owned-folder"),"saved-file")
        c.submit_save.assert_not_called()

    def test_stage_saves_when_owned_folder_is_empty(self):
        c=mock.Mock()
        c.list_folder.return_value=[]
        c.submit_save.return_value="task"
        c.poll_save.return_value="saved"
        f=api.ShareFile("fid-1","share-token","n.bin",25,"dir/n.bin")
        self.assertEqual(p.stage_one(c,"share","token",f,"owned-folder"),"saved")
        c.submit_save.assert_called_once_with("share","token",f,"owned-folder")

    def test_cleanup_requires_verified_state(self):
        c,g=mock.Mock(),mock.Mock()
        g.read_json.return_value=({"schema":1,"files":[]},None)
        records=[{"file_id":"a","quark_fid":"qa","status":"ACTIVE"},
                 {"file_id":"b","quark_fid":"qb","status":"VERIFIED"}]
        done=p.clean_verified(c,g,"task",records)
        self.assertEqual(done,{"b"})
        c.delete_staged.assert_called_once_with(["qb"])

if __name__=="__main__":
    unittest.main()
