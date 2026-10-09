#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

TASK_ROOT = Path(__file__).resolve().parent
DATA_ROOT = TASK_ROOT / "data"
DEFAULT_MAX_FILE_MIB = 90
DEFAULT_MAX_TOTAL_MIB = 500


def fail(message: str) -> "NoReturn":
    raise SystemExit(message)


def validate_source_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme.lower() != "https":
        raise ValueError("source URL must use https://")
    if not parsed.hostname:
        raise ValueError("source URL must include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("credential-bearing Git URLs are not allowed")
    host = parsed.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("localhost sources are not allowed")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_unspecified):
        raise ValueError("private/local IP sources are not allowed")
    if not parsed.path or parsed.path == "/":
        raise ValueError("source URL must include a repository path")
    return value


def slug_component(value: str) -> str:
    value = unquote(value).strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value)
    value = value.strip("-.")
    if not value or value in {".", ".."}:
        raise ValueError(f"invalid destination component derived from {value!r}")
    return value


def default_destination(source_url: str) -> str:
    parsed = urlparse(validate_source_url(source_url))
    host = slug_component(parsed.hostname or "")
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        raise ValueError("source URL must include a repository path")
    if parts[-1].endswith(".git"):
        parts[-1] = parts[-1][:-4]
    cleaned = [slug_component(part) for part in parts]
    return "/".join([host, *cleaned])


def destination_path(destination: str) -> Path:
    raw = Path(destination)
    if raw.is_absolute() or not destination.strip():
        raise ValueError("destination must be a non-empty relative path")
    if any(part in {"", ".", ".."} for part in raw.parts):
        raise ValueError("destination must not contain dot or parent components")
    cleaned = Path(*(slug_component(part) for part in raw.parts))
    return DATA_ROOT / cleaned


def run_git(args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        stderr = process.stderr.strip()
        raise RuntimeError(f"git {' '.join(args[:3])} failed: {stderr or 'unknown error'}")
    return process.stdout.strip()


def collect_submodules(repo: Path) -> list[dict[str, str]]:
    raw = run_git(["ls-files", "--stage", "-z"], cwd=repo)
    items: list[dict[str, str]] = []
    for entry in raw.split("\0"):
        if not entry:
            continue
        meta, sep, path = entry.partition("\t")
        if not sep:
            continue
        fields = meta.split()
        if len(fields) >= 2 and fields[0] == "160000":
            items.append({"path": path, "commit": fields[1]})
    return sorted(items, key=lambda item: item["path"])


def snapshot_stats(repo: Path, max_file_bytes: int, max_total_bytes: int) -> dict[str, int]:
    files = 0
    symlinks = 0
    total_bytes = 0
    for root, dirs, names in os.walk(repo, topdown=True, followlinks=False):
        root_path = Path(root)
        if root_path == repo:
            dirs[:] = [name for name in dirs if name != ".git"]
        for name in names:
            path = root_path / name
            if path.is_symlink():
                symlinks += 1
                size = path.lstat().st_size
            elif path.is_file():
                files += 1
                size = path.stat().st_size
                if size > max_file_bytes:
                    relative = path.relative_to(repo)
                    raise ValueError(f"file exceeds size guard ({size} bytes): {relative}")
            else:
                continue
            total_bytes += size
            if total_bytes > max_total_bytes:
                raise ValueError(f"snapshot exceeds total size guard ({max_total_bytes} bytes)")
    return {"regular_files": files, "symlinks": symlinks, "payload_bytes": total_bytes}


def copy_snapshot(repo: Path, target: Path) -> None:
    def ignore(path: str, names: list[str]) -> set[str]:
        if Path(path) == repo and ".git" in names:
            return {".git"}
        return set()

    shutil.copytree(repo, target, symlinks=True, ignore=ignore)


def import_snapshot(
    source_url: str,
    *,
    branch: str | None = None,
    destination: str | None = None,
    max_file_mib: int = DEFAULT_MAX_FILE_MIB,
    max_total_mib: int = DEFAULT_MAX_TOTAL_MIB,
) -> Path:
    source_url = validate_source_url(source_url)
    destination = destination or default_destination(source_url)
    target_root = destination_path(destination)
    if target_root.exists():
        raise FileExistsError(f"mirror destination already exists: {target_root.relative_to(TASK_ROOT.parent)}")
    if max_file_mib <= 0 or max_total_mib <= 0:
        raise ValueError("size guards must be positive")

    env = os.environ.copy()
    env["GIT_LFS_SKIP_SMUDGE"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"

    with tempfile.TemporaryDirectory(prefix="web-ingest-git-mirror-") as tmp:
        repo = Path(tmp) / "source"
        command = ["clone", "--depth", "1", "--single-branch"]
        if branch:
            command.extend(["--branch", branch])
        command.extend([source_url, str(repo)])
        run_git(command, env=env)

        commit = run_git(["rev-parse", "HEAD"], cwd=repo)
        tree = run_git(["rev-parse", "HEAD^{tree}"], cwd=repo)
        detected_branch = run_git(["branch", "--show-current"], cwd=repo) or None
        commit_time = run_git(["show", "-s", "--format=%cI", "HEAD"], cwd=repo)
        submodules = collect_submodules(repo)
        stats = snapshot_stats(
            repo,
            max_file_bytes=max_file_mib * 1024 * 1024,
            max_total_bytes=max_total_mib * 1024 * 1024,
        )

        target_root.mkdir(parents=True, exist_ok=False)
        snapshot = target_root / "snapshot"
        copy_snapshot(repo, snapshot)

        metadata = {
            "schema_version": 1,
            "kind": "public-git-file-snapshot",
            "source_url": source_url,
            "source_host": urlparse(source_url).hostname,
            "requested_branch": branch,
            "source_branch": detected_branch,
            "source_commit": commit,
            "source_tree": tree,
            "source_commit_time": commit_time,
            "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "snapshot_path": "snapshot",
            "history_policy": "working-tree-only; source .git history excluded",
            "lfs_policy": "skip-smudge; preserve pointer files",
            "submodule_policy": "not initialized; gitlink commits recorded",
            "size_guard": {
                "max_file_mib": max_file_mib,
                "max_total_mib": max_total_mib,
            },
            "stats": stats,
            "submodules": submodules,
        }
        (target_root / "source.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return target_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a one-shot file snapshot from a public HTTPS Git repository")
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--branch", help="source branch; omit to use the repository default branch")
    parser.add_argument("--destination", help="relative destination below git-mirror/data; defaults to host/source path")
    parser.add_argument("--max-file-mib", type=int, default=DEFAULT_MAX_FILE_MIB)
    parser.add_argument("--max-total-mib", type=int, default=DEFAULT_MAX_TOTAL_MIB)
    args = parser.parse_args()

    try:
        path = import_snapshot(
            args.source_url,
            branch=args.branch,
            destination=args.destination,
            max_file_mib=args.max_file_mib,
            max_total_mib=args.max_total_mib,
        )
    except (ValueError, FileExistsError, RuntimeError) as exc:
        print(f"git-mirror: {exc}", file=sys.stderr)
        return 2

    print(path.relative_to(TASK_ROOT.parent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
