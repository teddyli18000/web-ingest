#!/usr/bin/env python3
"""Quark share scanning and tool-owned staging API, adapted from MIT Gopeed client."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

API = "https://drive-pc.quark.cn/1/clouddrive"
SHARE = "https://pan.quark.cn/1/clouddrive"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "quark-cloud-drive/2.5.20 Chrome/100.0.4896.160 Electron/18.3.5.4-b478491100 Safari/537.36")
PAGE_SIZE = 100


class QuarkAuthRequired(RuntimeError):
    pass


class QuarkTemporaryError(RuntimeError):
    pass


class QuarkProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ShareFile:
    fid: str
    fid_token: str
    name: str
    size: int
    relative_path: str


def parse_share_url(value: str) -> tuple[str, str]:
    url = urllib.parse.urlsplit(value.strip())
    if url.scheme != "https" or url.hostname not in {"pan.quark.cn", "drive.quark.cn"}:
        raise ValueError("Expected an HTTPS Quark share URL")
    match = re.fullmatch(r"/s/([a-zA-Z0-9]+)/*", url.path)
    if match is None:
        raise ValueError("Expected a Quark /s/<share-id> URL")
    query = urllib.parse.parse_qs(url.query)
    code = next((query[key][0] for key in ("pwd", "password", "pw") if query.get(key)), "")
    return match.group(1), code


def merge_puus(cookie: str, value: str) -> str:
    current = [(a.strip(), b.strip()) for item in cookie.split(";") if "=" in item
               for a, b in [item.split("=", 1)] if a.strip() != "__puus"]
    current.append(("__puus", value))
    return "; ".join(f"{k}={v}" for k, v in current)


def quark_transport(method: str, url: str, headers: dict, payload: dict | None) -> tuple[int, dict, list[str]]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            return res.status, json.load(res), res.headers.get_all("Set-Cookie") or []
    except urllib.error.HTTPError as exc:
        raw = exc.read(1 << 16)
        try:
            result = json.loads(raw)
        except ValueError:
            result = {"code": -1}
        return exc.code, result, exc.headers.get_all("Set-Cookie") or []


class Client:
    def __init__(self, cookie: str, transport=quark_transport):
        self.cookie = cookie.strip()
        if "__puus=" not in self.cookie:
            raise QuarkAuthRequired("Quark browser login is required")
        self.transport = transport

    def call(self, method: str, path: str, payload: dict | None = None, *, share: bool = False,
             params: dict | None = None) -> dict:
        query = {"pr": "ucpro", "fr": "pc"}
        query.update(params or {})
        url = (SHARE if share else API) + path + "?" + urllib.parse.urlencode(query)
        headers = {"Cookie": self.cookie, "User-Agent": UA, "Referer": "https://pan.quark.cn/",
                   "Origin": "https://pan.quark.cn", "Accept": "application/json,*/*",
                   "Content-Type": "application/json;charset=UTF-8"}
        status, result, updated = self.transport(method, url, headers, payload)
        for raw in updated:
            pair = raw.split(";", 1)[0].strip()
            if pair.startswith("__puus="):
                self.cookie = merge_puus(self.cookie, pair[len("__puus="):])
        code = result.get("code")
        if code in (10000, 40001) or status == 401:
            raise QuarkAuthRequired("Quark browser session expired")
        if status in (429, 500, 502, 503, 504) or code == 23018:
            raise QuarkTemporaryError(f"Quark temporarily rejected request: HTTP {status}, code {code}")
        if status >= 400 or code != 0:
            raise QuarkProviderError(f"Quark request failed: HTTP {status}, code {code}")
        return result["data"]

    def share_token(self, share_id: str, code: str) -> str:
        data = self.call("POST", "/share/sharepage/token", {"pwd_id": share_id, "passcode": code}, share=True)
        return str(data["stoken"])

    def page(self, share_id: str, token: str, folder: str, page: int) -> list[dict]:
        data = self.call("GET", "/share/sharepage/detail", share=True, params={
            "pwd_id": share_id, "stoken": token, "pdir_fid": folder or "0",
            "_page": page, "_size": PAGE_SIZE, "_sort": "file_type:asc,updated_at:desc",
        })
        return data["list"]

    def scan(self, share_id: str, token: str) -> list[ShareFile]:
        output = []
        pending = [("0", "")]
        while pending:
            folder, parent = pending.pop()
            index = 1
            while True:
                items = self.page(share_id, token, folder, index)
                for item in items:
                    name = str(item["file_name"])
                    if item.get("dir"):
                        pending.append((str(item["fid"]), parent + name + "/"))
                    else:
                        output.append(ShareFile(str(item["fid"]), str(item["share_fid_token"]),
                                                name, int(item["size"]), parent + name))
                if len(items) < PAGE_SIZE:
                    break
                index += 1
        return output

    def list_folder(self, fid: str) -> list[dict]:
        all_items = []
        page = 1
        while True:
            data = self.call("GET", "/file/sort", params={
                "pdir_fid": fid, "_page": page, "_size": PAGE_SIZE,
                "_sort": "file_type:asc,file_name:asc",
            })
            items = data["list"]
            all_items.extend(items)
            if len(items) < PAGE_SIZE:
                return all_items
            page += 1

    def ensure_folder(self, parent: str, name: str) -> str:
        existing = [item for item in self.list_folder(parent) if item.get("dir") and item.get("file_name") == name]
        if len(existing) == 1:
            return str(existing[0]["fid"])
        if existing:
            raise QuarkProviderError("Quark tool-owned staging folder is ambiguous")
        result = self.call("POST", "/file", {"pdir_fid": parent, "file_name": name, "dir": True})
        return str(result["fid"])

    def space_available(self) -> int:
        data = self.call("GET", "/member", params={"fetch_subscribe": "true", "fetch_identity": "true"})
        return max(0, int(data["total_capacity"]) - int(data["use_capacity"]))

    def submit_save(self, share_id: str, stoken: str, file: ShareFile, folder_id: str) -> str:
        data = self.call("POST", "/share/sharepage/save", {
            "fid_list": [file.fid], "fid_token_list": [file.fid_token],
            "to_pdir_fid": folder_id, "pwd_id": share_id, "stoken": stoken,
            "pdir_fid": "0", "scene": "link",
        })
        return str(data["task_id"])

    def poll_save(self, task_id: str, *, attempts: int = 30, sleep=time.sleep) -> str:
        for i in range(attempts):
            data = self.call("GET", "/task", params={"task_id": task_id})
            if data.get("status") == 2:
                return str(data["save_as"]["save_as_top_fids"][0])
            if data.get("status") == 3:
                raise QuarkTemporaryError("Quark cloud save rejected this file")
            if i + 1 < attempts:
                sleep(1)
        raise QuarkTemporaryError("Quark cloud save is still processing")

    def download_link(self, fid: str) -> str:
        values = self.call("POST", "/file/download", {"fids": [fid]})
        if isinstance(values, dict):
            values = values["list"]
        match = next((item for item in values if str(item.get("fid")) == fid and item.get("download_url")), None)
        if match is None and len(values) == 1:
            match = values[0]
        if match is None or not match.get("download_url"):
            raise QuarkTemporaryError("Quark signed download link is unavailable")
        return str(match["download_url"])

    def delete_staged(self, fids: list[str]) -> None:
        self.call("POST", "/file/delete", {"action_type": 2, "filelist": fids, "exclude_fids": []})
