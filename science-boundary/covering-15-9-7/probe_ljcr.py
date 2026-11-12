#!/usr/bin/env python3
"""Probe Zenodo byte-range access to public LJCR constructions."""
import json
import urllib.request
import urllib.error

api="https://zenodo.org/api/records/19735294"
with urllib.request.urlopen(api,timeout=60) as f:
    d=json.load(f)
for entry in d["files"]:
    print("file:",entry["key"],entry["size"],flush=True)
    if entry["key"] == "covers.json":
        url=entry["links"]["self"]
        print("url:",url,flush=True)
        req=urllib.request.Request(url,headers={"Range":"bytes=0-10485759","User-Agent":"p015-scientific-research"})
        with urllib.request.urlopen(req,timeout=90) as f:
            data=f.read(10485760)
            print("status:",f.status,"content-range:",f.headers.get("Content-Range"),"type:",f.headers.get("Content-Type"),flush=True)
            print("prefix:",repr(data[:350]),flush=True)
            print("target-position:",data.find(b'C(15,10,8)'),flush=True)
            print("other-target:",data.find(b'C(15,9,7)'),flush=True)
            print("trailing:",repr(data[-100:]),flush=True)
