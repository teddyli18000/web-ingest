#!/usr/bin/env python3
"""Minimal Google Drive folder operations for Quark's own resumable task root."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

BASE = "https://www.googleapis.com/drive/v3/files"
FOLDER_MIME = "application/vnd.google-apps.folder"


class DriveFolders:
    def __init__(self, access_token: str, request=None):
        self.token = access_token
        self.request = request or self._request
        self.cache = {}

    def _request(self, method: str, url: str, obj=None):
        raw = json.dumps(obj).encode() if obj is not None else None
        req = urllib.request.Request(url, data=raw, method=method, headers={
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=45) as response:
            return json.load(response)

    def folder(self, parent: str, name: str) -> str:
        key = (parent, name)
        if key in self.cache:
            return self.cache[key]
        escaped = name.replace("\\", "\\\\").replace("'", "\\'")
        query = f"name = '{escaped}' and mimeType = '{FOLDER_MIME}' and '{parent}' in parents and trashed = false"
        params = urllib.parse.urlencode({"q":query, "fields":"nextPageToken,files(id,name,mimeType,parents)", "page_size":100})
        result = self.request("GET", BASE + "?" + params)
        matches = result.get("files", [])
        if len(matches) > 1:
            raise ValueError("Drive destination contains ambiguous same-name folders")
        if matches:
            fid = str(matches[0]["id"])
        else:
            value = self.request("POST",BASE+"?fields=id",{"name":name,"mimeType":FOLDER_MIME,"parents":[parent]})
            fid = str(value["id"])
        self.cache[key] = fid
        return fid

    def parent_path(self, root: str, path: str) -> str:
        fid = root
        for name in path.strip("/").split("/"):
            if name:
                fid = self.folder(fid, name)
        return fid
