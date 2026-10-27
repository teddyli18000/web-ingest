#!/usr/bin/env python3
"""GitHub-backed per-file relay state and deterministic worker dispatch."""
from __future__ import annotations

import argparse
import base64
import copy
import datetime as dt
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Callable

import relay_state
import scheduler

FILE_STATE_ROOT = "baidu-drive/state/files"
DEFAULT_FILE_WORKFLOW = "baidu-drive-file-worker.yml"
IMMUTABLE_FIELDS = (
    "task_id",
    "file_id",
    "batch_id",
    "logical_path",
    "parent_path",
    "name",
    "size",
    "md5",
    "baidu_staging_path",
    "drive_parent_id",
)


class ControlError(RuntimeError):
    pass


class GitHubHTTPError(ControlError):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


class GitHubRepo:
    def __init__(self, repository: str, token: str):
        if not repository or not token:
            raise ControlError("GITHUB_REPOSITORY/GITHUB_TOKEN is missing")
        self.repository = repository
        self.api = f"https://api.github.com/repos/{repository}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "web-ingest-baidu-drive-relay",
        }

    def _request(self, method: str, url: str, obj: Any = None) -> Any:
        data = None
        headers = dict(self.headers)
        if obj is not None:
            data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, method=method, data=data, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read(1024).decode("utf-8", errors="replace")
            raise GitHubHTTPError(exc.code, f"GitHub API {method} failed: HTTP {exc.code}: {detail[:200]}") from None
        return json.loads(payload.decode("utf-8")) if payload else None

    def read_record(self, task_id: str, file_id: str) -> tuple[dict[str, Any] | None, str | None]:
        path = relay_state.state_path(task_id, file_id)
        url = f"{self.api}/contents/{urllib.parse.quote(path, safe='/')}?ref=main"
        try:
            item = self._request("GET", url)
        except GitHubHTTPError as exc:
            if exc.code == 404:
                return None, None
            raise
        try:
            value = json.loads(base64.b64decode(item["content"]).decode("utf-8"))
        except (KeyError, UnicodeDecodeError, ValueError) as exc:
            raise ControlError(f"invalid relay state at {path}: {exc}") from None
        if not isinstance(value, dict):
            raise ControlError(f"relay state at {path} is not an object")
        return value, str(item.get("sha") or "") or None

    def list_records(self, task_id: str) -> list[dict[str, Any]]:
        task = relay_state._safe_id(task_id, "task id")
        path = f"{FILE_STATE_ROOT}/{task}"
        url = f"{self.api}/contents/{urllib.parse.quote(path, safe='/')}?ref=main"
        try:
            items = self._request("GET", url)
        except GitHubHTTPError as exc:
            if exc.code == 404:
                return []
            raise
        if not isinstance(items, list):
            raise ControlError("relay state directory response is not a list")
        result: list[dict[str, Any]] = []
        for item in items:
            name = str(item.get("name") or "")
            if item.get("type") != "file" or not name.endswith(".json"):
                continue
            file_id = name[:-5]
            record, _ = self.read_record(task, file_id)
            if record is not None:
                result.append(record)
        result.sort(key=lambda value: str(value.get("file_id") or ""))
        return result

    def _put_record(self, task_id: str, file_id: str, value: dict[str, Any], message: str, sha: str | None) -> None:
        path = relay_state.state_path(task_id, file_id)
        content = base64.b64encode((json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")).decode("ascii")
        body: dict[str, Any] = {"message": message, "content": content, "branch": "main"}
        if sha:
            body["sha"] = sha
        self._request("PUT", f"{self.api}/contents/{urllib.parse.quote(path, safe='/')}", body)

    def mutate_record(
        self,
        task_id: str,
        file_id: str,
        mutator: Callable[[dict[str, Any]], dict[str, Any]],
        message: str,
        retries: int = 5,
    ) -> dict[str, Any]:
        for attempt in range(retries):
            current, sha = self.read_record(task_id, file_id)
            if current is None:
                raise ControlError(f"relay state for {file_id} does not exist")
            updated = mutator(copy.deepcopy(current))
            try:
                self._put_record(task_id, file_id, updated, message, sha)
                return updated
            except GitHubHTTPError as exc:
                if exc.code not in (409, 422) or attempt + 1 >= retries:
                    raise
        raise ControlError(f"failed to update relay state for {file_id}")

    def ensure_record(self, task_id: str, source: dict[str, Any], now: dt.datetime) -> dict[str, Any]:
        candidate = relay_state.new_record(task_id, source, now)
        file_id = candidate["file_id"]
        for attempt in range(5):
            current, sha = self.read_record(task_id, file_id)
            if current is not None:
                assert_same_source(current, candidate)
                return current
            try:
                self._put_record(task_id, file_id, candidate, f"baidu-drive: register relay file {file_id}", sha)
                return candidate
            except GitHubHTTPError as exc:
                if exc.code not in (409, 422) or attempt == 4:
                    raise
        raise ControlError(f"failed to register relay file {file_id}")

    def dispatch_file_worker(self, task_id: str, file_id: str, lease_id: str, workflow: str = DEFAULT_FILE_WORKFLOW) -> None:
        workflow = pathlib.PurePosixPath(workflow).name
        self._request(
            "POST",
            f"{self.api}/actions/workflows/{urllib.parse.quote(workflow)}/dispatches",
            {
                "ref": "main",
                "inputs": {
                    "task_id": task_id,
                    "file_id": file_id,
                    "lease_id": lease_id,
                },
            },
        )


def assert_same_source(existing: dict[str, Any], candidate: dict[str, Any]) -> None:
    for field in IMMUTABLE_FIELDS:
        if existing.get(field) != candidate.get(field):
            raise ControlError(f"relay source identity changed for {candidate.get('file_id')}: {field}")


def sync_manifest(repo: Any, task_id: str, manifest: list[dict[str, Any]], now: dt.datetime) -> list[dict[str, Any]]:
    if not isinstance(manifest, list):
        raise ControlError("relay manifest must be a list")
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for source in manifest:
        if not isinstance(source, dict):
            raise ControlError("relay manifest entry must be an object")
        file_id = str(source.get("file_id") or "")
        if file_id in seen:
            raise ControlError(f"duplicate relay manifest file {file_id}")
        seen.add(file_id)
        result.append(repo.ensure_record(task_id, source, now))
    return result


def reset_retryable_files(repo: Any, task_id: str, now: dt.datetime) -> int:
    """Re-arm retryable files only after an explicit human/task retry request."""
    reset = 0
    for record in repo.list_records(task_id):
        if record.get("status") != relay_state.FAILED_RETRYABLE:
            continue
        file_id = str(record.get("file_id") or "")
        repo.mutate_record(
            task_id,
            file_id,
            lambda current: relay_state.reset_retryable(current, now),
            f"baidu-drive: re-arm retryable relay file {file_id}",
        )
        reset += 1
    return reset


def make_lease_id(run_id: str) -> str:
    run = "".join(ch for ch in str(run_id or "local") if ch.isalnum())[-20:] or "local"
    return f"w-{run}-{uuid.uuid4().hex[:12]}"


def schedule_once(
    repo: Any,
    task_id: str,
    now: dt.datetime,
    run_id: str,
    workflow: str = DEFAULT_FILE_WORKFLOW,
    policy: scheduler.Policy = scheduler.Policy(),
) -> list[tuple[str, str]]:
    records = repo.list_records(task_id)
    chosen = scheduler.choose_files(records, now, policy)
    dispatched: list[tuple[str, str]] = []
    for file_id in chosen:
        lease_id = make_lease_id(run_id)
        claimed = repo.mutate_record(
            task_id,
            file_id,
            lambda current, lease=lease_id: relay_state.claim(
                current,
                lease,
                now,
                policy.stale_heartbeat_seconds,
                policy.max_retryable_failures,
            ),
            f"baidu-drive: lease relay file {file_id}",
        )
        if claimed.get("lease_id") != lease_id:
            raise ControlError(f"relay lease for {file_id} was not persisted")
        try:
            repo.dispatch_file_worker(task_id, file_id, lease_id, workflow)
        except Exception:
            try:
                repo.mutate_record(
                    task_id,
                    file_id,
                    lambda current, lease=lease_id: relay_state.pause(current, lease, now, "worker dispatch failed"),
                    f"baidu-drive: release undispatched relay file {file_id}",
                )
            except Exception:
                pass
            raise
        dispatched.append((file_id, lease_id))
    return dispatched


def verified_results(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for record in records:
        if record.get("status") != relay_state.VERIFIED:
            continue
        file_id = str(record.get("file_id") or "")
        drive_id = str(record.get("drive_file_id") or "")
        if not file_id or not drive_id:
            raise ControlError("verified relay record is missing file or Drive ID")
        result.append({"file_id": file_id, "drive_id": drive_id})
    result.sort(key=lambda value: value["file_id"])
    return result


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    sync = sub.add_parser("sync-manifest")
    sync.add_argument("--task-id", required=True)
    sync.add_argument("--manifest", required=True)

    schedule_cmd = sub.add_parser("schedule")
    schedule_cmd.add_argument("--task-id", required=True)
    schedule_cmd.add_argument("--workflow", default=DEFAULT_FILE_WORKFLOW)

    results = sub.add_parser("results")
    results.add_argument("--task-id", required=True)
    results.add_argument("--output", required=True)

    args = parser.parse_args(argv)
    repo = GitHubRepo(os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", ""))
    now = utc_now()

    if args.command == "sync-manifest":
        with open(args.manifest, encoding="utf-8") as handle:
            manifest = json.load(handle)
        sync_manifest(repo, args.task_id, manifest, now)
        return 0
    if args.command == "schedule":
        schedule_once(repo, args.task_id, now, os.environ.get("GITHUB_RUN_ID", "local"), args.workflow)
        return 0
    if args.command == "results":
        values = verified_results(repo.list_records(args.task_id))
        output = pathlib.Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
