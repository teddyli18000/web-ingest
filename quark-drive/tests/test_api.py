from __future__ import annotations

import sys
from pathlib import Path
import unittest
from urllib.parse import urlsplit, parse_qs

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import api


class QuarkAPITests(unittest.TestCase):
    def test_share_url_and_cookie_rotation(self):
        self.assertEqual(api.parse_share_url("https://pan.quark.cn/s/ABC12?pwd=Q9"), ("ABC12","Q9"))
        self.assertEqual(api.merge_puus("foo=bar; __puus=old", "fresh"), "foo=bar; __puus=fresh")
        with self.assertRaises(ValueError):
            api.parse_share_url("http://pan.quark.cn/s/abc")

    def test_share_scan_recurses_and_uses_all_pages(self):
        calls=[]
        def fake(method,url,headers,payload):
            parts=urlsplit(url); q=parse_qs(parts.query)
            calls.append((parts.path,q.get("pdir_fid",["0"])[0]))
            if parts.path.endswith("/share/sharepage/token"):
                return 200,{"code":0,"data":{"stoken":"token"}},["__puus=refreshed; Path=/"]
            if parts.path.endswith("/share/sharepage/detail"):
                folder=q["pdir_fid"][0]
                if folder=="0":
                    return 200,{"code":0,"data":{"list":[{"fid":"folder","file_name":"root","dir":True},
                      {"fid":"f0","file_name":"top.txt","share_fid_token":"tok0","size":3}]}},[]
                return 200,{"code":0,"data":{"list":[
                    {"fid":"f1","file_name":"nested.txt","share_fid_token":"tok1","size":7}
                ]}},[]
            raise AssertionError("unexpected endpoint")
        client=api.Client("foo=bar; __puus=old",fake)
        token=client.share_token("id","")
        files=client.scan("id",token)
        self.assertEqual(sorted(x.relative_path for x in files),["root/nested.txt","top.txt"])
        self.assertEqual(client.cookie,"foo=bar; __puus=refreshed")
        self.assertEqual(token,"token")

    def test_staging_and_refresh_request_payload(self):
        seen=[]
        def fake(method,url,headers,payload):
            seen.append((urlsplit(url).path,method,payload))
            if urlsplit(url).path.endswith("/share/sharepage/save"):
                return 200,{"code":0,"data":{"task_id":"t1"}},[]
            if urlsplit(url).path.endswith("/task"):
                return 200,{"code":0,"data":{"status":2,"save_as":{"save_as_top_fids":["saved1"]}}},[]
            if urlsplit(url).path.endswith("/file/download"):
                return 200,{"code":0,"data":[{"fid":"saved1","download_url":"https://cdn.invalid/file?token=secret"}]},[]
            raise AssertionError("unexpected endpoint")
        client=api.Client("__puus=x",fake)
        f=api.ShareFile("source","ftok","name",20,"name")
        self.assertEqual(client.poll_save(client.submit_save("id","token",f,"folder"),sleep=lambda _:None),"saved1")
        self.assertEqual(client.download_link("saved1"),"https://cdn.invalid/file?token=secret")
        self.assertEqual(seen[0][2]["fid_token_list"],["ftok"])
        self.assertEqual(seen[0][2]["to_pdir_fid"],"folder")

if __name__=="__main__":
    unittest.main()
