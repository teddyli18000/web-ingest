#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parent
DATA_ROOT = TASK_ROOT / "data"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def measure(snapshot: Path) -> dict[str, int]:
    files = 0
    symlinks = 0
    total_bytes = 0
    for root, _, names in os.walk(snapshot, followlinks=False):
        root_path = Path(root)
        for name in names:
            path = root_path / name
            if path.is_symlink():
                symlinks += 1
                total_bytes += path.lstat().st_size
            elif path.is_file():
                files += 1
                total_bytes += path.stat().st_size
    return {"regular_files": files, "symlinks": symlinks, "payload_bytes": total_bytes}


def validate_one(metadata_path: Path) -> list[str]:
    errors: list[str] = []
    root = metadata_path.parent
    snapshot = root / "snapshot"
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{metadata_path}: invalid JSON: {exc}"]

    if payload.get("schema_version") != 1:
        errors.append(f"{metadata_path}: schema_version must be 1")
    if payload.get("kind") != "public-git-file-snapshot":
        errors.append(f"{metadata_path}: unexpected kind")
    source_url = payload.get("source_url")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        errors.append(f"{metadata_path}: source_url must be public HTTPS provenance")
    for field in ("source_commit", "source_tree"):
        value = payload.get(field)
        if not isinstance(value, str) or not SHA_RE.fullmatch(value):
            errors.append(f"{metadata_path}: {field} must be a 40-character lowercase Git SHA")
    if payload.get("snapshot_path") != "snapshot":
        errors.append(f"{metadata_path}: snapshot_path must be 'snapshot'")
    if not snapshot.is_dir():
        errors.append(f"{metadata_path}: snapshot directory is missing")
        return errors

    stats = payload.get("stats")
    if not isinstance(stats, dict):
        errors.append(f"{metadata_path}: stats object is missing")
    else:
        actual = measure(snapshot)
        for key, value in actual.items():
            if stats.get(key) != value:
                errors.append(f"{metadata_path}: stats.{key}={stats.get(key)!r}, actual={value}")

    submodules = payload.get("submodules")
    if not isinstance(submodules, list):
        errors.append(f"{metadata_path}: submodules must be a list")
    else:
        for index, item in enumerate(submodules):
            if not isinstance(item, dict):
                errors.append(f"{metadata_path}: submodules[{index}] must be an object")
                continue
            if not isinstance(item.get("path"), str) or not item["path"]:
                errors.append(f"{metadata_path}: submodules[{index}].path is invalid")
            commit = item.get("commit")
            if not isinstance(commit, str) or not SHA_RE.fullmatch(commit):
                errors.append(f"{metadata_path}: submodules[{index}].commit is invalid")
    return errors


def main() -> int:
    if not DATA_ROOT.exists():
        print("git-mirror: no snapshots yet")
        return 0
    metadata_files = sorted(DATA_ROOT.glob("**/source.json"))
    if not metadata_files:
        print("git-mirror: no snapshots yet")
        return 0

    errors: list[str] = []
    for metadata_path in metadata_files:
        errors.extend(validate_one(metadata_path))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"git-mirror: validated {len(metadata_files)} snapshot(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
