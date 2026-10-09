#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from import_snapshot import default_destination, destination_path, validate_source_url

DEFAULT_MAX_ASSET_MIB = 90
DEFAULT_MAX_RELEASE_MIB = 500
USER_AGENT = "teddyli18000-web-ingest-git-mirror/1"


def github_repo(source_url: str) -> tuple[str, str] | None:
    parsed = urlparse(validate_source_url(source_url))
    if (parsed.hostname or "").lower() != "github.com":
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        return None
    owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not owner or not repo:
        return None
    return owner, repo


def safe_name(value: str) -> str:
    name = Path(value.replace("\\", "/")).name
    name = re.sub(r"[\x00-\x1f]+", "-", name).strip()
    if not name or name in {".", ".."}:
        return "asset"
    return name


def api_json(url: str, token: str | None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def download_asset(url: str, target: Path, *, token: str | None, max_bytes: int) -> tuple[int, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/octet-stream"}
    if token and urlparse(url).hostname in {"github.com", "api.github.com"}:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    digest = hashlib.sha256()
    written = 0
    try:
        with urlopen(request, timeout=60) as response, target.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise ValueError(f"asset exceeds size guard: {target.name}")
                digest.update(chunk)
                handle.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return written, digest.hexdigest()


def render_readme(release: dict, assets: list[dict]) -> str:
    title = release.get("name") or release.get("tag_name") or "Latest release"
    tag = release.get("tag_name") or ""
    published = release.get("published_at") or release.get("created_at") or ""
    html_url = release.get("html_url") or ""
    body = release.get("body") or ""

    lines = [
        f"# {title}",
        "",
        f"- Tag: `{tag}`" if tag else "- Tag: —",
        f"- Published: {published}" if published else "- Published: —",
        f"- Source: {html_url}" if html_url else "- Source: —",
        "",
    ]
    if body.strip():
        lines.extend(["## Release notes", "", body.rstrip(), ""])
    if assets:
        lines.extend(["## Assets", ""])
        for asset in assets:
            name = asset.get("name") or "asset"
            local = asset.get("local_path")
            if local:
                lines.append(f"- [{name}]({local})")
            else:
                reason = asset.get("status") or "not mirrored"
                source = asset.get("browser_download_url") or ""
                suffix = f" — {source}" if source else ""
                lines.append(f"- {name} — {reason}{suffix}")
        lines.append("")
    return "\n".join(lines)


def collect_latest_release(
    source_url: str,
    *,
    destination: str | None = None,
    max_asset_mib: int = DEFAULT_MAX_ASSET_MIB,
    max_release_mib: int = DEFAULT_MAX_RELEASE_MIB,
) -> Path | None:
    repo_id = github_repo(source_url)
    if repo_id is None:
        print("git-mirror: latest release collection currently skipped for non-GitHub source")
        return None
    if max_asset_mib <= 0 or max_release_mib <= 0:
        raise ValueError("release size guards must be positive")

    owner, repo = repo_id
    destination = destination or default_destination(source_url)
    mirror_root = destination_path(destination)
    if not (mirror_root / "snapshot").is_dir():
        raise FileNotFoundError(f"snapshot must exist before release collection: {mirror_root}")

    token = os.environ.get("GITHUB_TOKEN") or None
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        release = api_json(api_url, token)
    except HTTPError as exc:
        if exc.code == 404:
            print("git-mirror: source has no latest GitHub release")
            return None
        raise RuntimeError(f"GitHub release API failed: HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"GitHub release API failed: {exc.reason}") from exc

    release_root = mirror_root / "release"
    if release_root.exists():
        raise FileExistsError(f"release destination already exists: {release_root}")
    assets_dir = release_root / "assets"
    assets_dir.mkdir(parents=True)

    total_limit = max_release_mib * 1024 * 1024
    per_asset_limit = max_asset_mib * 1024 * 1024
    total_written = 0
    captured_assets: list[dict] = []

    for raw_asset in release.get("assets") or []:
        name = safe_name(str(raw_asset.get("name") or "asset"))
        size = raw_asset.get("size")
        item = {
            "name": name,
            "browser_download_url": raw_asset.get("browser_download_url"),
            "content_type": raw_asset.get("content_type"),
            "source_size": size,
        }
        if not isinstance(size, int) or size < 0:
            item["status"] = "not mirrored: invalid source size"
            captured_assets.append(item)
            continue
        if size > per_asset_limit:
            item["status"] = f"not mirrored: exceeds {max_asset_mib} MiB per-asset guard"
            captured_assets.append(item)
            continue
        if total_written + size > total_limit:
            item["status"] = f"not mirrored: exceeds {max_release_mib} MiB release guard"
            captured_assets.append(item)
            continue
        url = raw_asset.get("browser_download_url")
        if not isinstance(url, str) or not url.startswith("https://"):
            item["status"] = "not mirrored: invalid download URL"
            captured_assets.append(item)
            continue

        target = assets_dir / name
        if target.exists():
            stem, suffix = target.stem, target.suffix
            index = 2
            while target.exists():
                target = assets_dir / f"{stem}-{index}{suffix}"
                index += 1
        try:
            written, sha256 = download_asset(url, target, token=token, max_bytes=per_asset_limit)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            item["status"] = f"not mirrored: download failed ({type(exc).__name__})"
            captured_assets.append(item)
            continue

        total_written += written
        item.update({
            "status": "mirrored",
            "local_path": f"assets/{target.name}",
            "mirrored_size": written,
            "sha256": sha256,
        })
        captured_assets.append(item)

    if not any(assets_dir.iterdir()):
        assets_dir.rmdir()

    metadata = {
        "schema_version": 1,
        "kind": "public-github-latest-release",
        "source_repository": source_url,
        "release_api_url": api_url,
        "release_id": release.get("id"),
        "name": release.get("name"),
        "tag_name": release.get("tag_name"),
        "html_url": release.get("html_url"),
        "created_at": release.get("created_at"),
        "published_at": release.get("published_at"),
        "draft": release.get("draft"),
        "prerelease": release.get("prerelease"),
        "body": release.get("body") or "",
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "assets": captured_assets,
        "policy": "latest formal GitHub release only; GitHub-generated source archives are not duplicated",
    }
    (release_root / "release.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (release_root / "README.md").write_text(
        render_readme(release, captured_assets),
        encoding="utf-8",
    )
    return release_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Mirror the latest formal GitHub release beside a git-mirror snapshot")
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--destination", help="relative destination below git-mirror/data; defaults to host/source path")
    parser.add_argument("--max-asset-mib", type=int, default=DEFAULT_MAX_ASSET_MIB)
    parser.add_argument("--max-release-mib", type=int, default=DEFAULT_MAX_RELEASE_MIB)
    args = parser.parse_args()
    try:
        path = collect_latest_release(
            args.source_url,
            destination=args.destination,
            max_asset_mib=args.max_asset_mib,
            max_release_mib=args.max_release_mib,
        )
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        print(f"git-mirror: {exc}", file=sys.stderr)
        return 2
    if path is not None:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
