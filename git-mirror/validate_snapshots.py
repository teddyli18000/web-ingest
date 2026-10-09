#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parent
DATA_ROOT = TASK_ROOT / "data"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_release(root: Path) -> list[str]:
    release_root = root / "release"
    if not release_root.exists():
        return []

    errors: list[str] = []
    metadata_path = release_root / "release.json"
    readme_path = release_root / "README.md"
    if not metadata_path.is_file():
        errors.append(f"{release_root}: release.json is missing")
        return errors
    if not readme_path.is_file() or not readme_path.read_text(encoding="utf-8").strip():
        errors.append(f"{release_root}: README.md is missing or empty")

    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return errors + [f"{metadata_path}: invalid JSON: {exc}"]

    if payload.get("schema_version") != 1:
        errors.append(f"{metadata_path}: schema_version must be 1")
    if payload.get("kind") != "public-github-latest-release":
        errors.append(f"{metadata_path}: unexpected kind")
    if not isinstance(payload.get("body"), str):
        errors.append(f"{metadata_path}: body must be a string")
    if not isinstance(payload.get("tag_name"), str) or not payload.get("tag_name"):
        errors.append(f"{metadata_path}: tag_name is missing")

    assets = payload.get("assets")
    if not isinstance(assets, list):
        errors.append(f"{metadata_path}: assets must be a list")
        return errors

    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            errors.append(f"{metadata_path}: assets[{index}] must be an object")
            continue
        local = asset.get("local_path")
        if local is None:
            continue
        if not isinstance(local, str) or not local.startswith("assets/"):
            errors.append(f"{metadata_path}: assets[{index}].local_path is invalid")
            continue
        path = release_root / local
        if not path.is_file():
            errors.append(f"{metadata_path}: mirrored asset is missing: {local}")
            continue
        expected_size = asset.get("mirrored_size")
        if expected_size != path.stat().st_size:
            errors.append(f"{metadata_path}: mirrored asset size mismatch: {local}")
        expected_hash = asset.get("sha256")
        if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            errors.append(f"{metadata_path}: invalid SHA-256 for {local}")
        elif sha256_file(path) != expected_hash:
            errors.append(f"{metadata_path}: SHA-256 mismatch for {local}")
    return errors


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

    errors.extend(validate_release(root))
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
    print(f"git-mirror: validated {len(metadata_files)} mirror(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
