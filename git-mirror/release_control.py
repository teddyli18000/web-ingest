#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlparse, urlunparse
from urllib.request import Request, urlopen

from collect_latest_release import collect_latest_release
from import_snapshot import DATA_ROOT, default_destination, import_snapshot, validate_source_url
from validate_snapshots import validate_one

TASK_ROOT = Path(__file__).resolve().parent
README_PATH = TASK_ROOT / "README.md"
RELEASE_TAG = "git-mirror-live"
RELEASE_TITLE = "Git Mirror"
QUEUE_START = "<!-- mirror-queue:start -->"
QUEUE_END = "<!-- mirror-queue:end -->"
RESULT_START = "<!-- mirror-result:start -->"
RESULT_END = "<!-- mirror-result:end -->"
INDEX_START = "<!-- mirror-index:start -->"
INDEX_END = "<!-- mirror-index:end -->"
URL_RE = re.compile(r"https://[^\s<>()]+", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\((https://[^)]+)\)", re.IGNORECASE)


@dataclass(frozen=True)
class SourceInfo:
    clone_url: str
    web_url: str
    repository_name: str
    source_label: str
    description: str | None
    destination: str


@dataclass(frozen=True)
class RequestResult:
    request: str
    source_url: str | None
    label: str
    status: str
    message: str


def release_body(results: list[RequestResult] | None = None) -> str:
    if results is None:
        result_text = "No requests processed yet."
    elif not results:
        result_text = "No repository URLs were queued."
    else:
        icons = {"mirrored": "✅", "already_mirrored": "↪️", "duplicate": "↪️", "failed": "❌"}
        lines = []
        for item in results:
            icon = icons.get(item.status, "•")
            lines.append(f"- {icon} `{item.label}` — {item.message}")
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        result_text = f"Processed {stamp}\n\n" + "\n".join(lines)

    return f"""# Git Mirror

Paste one public HTTPS Git repository URL per line in **Queue**, then choose **Update release**.

Accepted forms include `https://github.com/owner/repo`, the same URL ending in `.git`, and trailing whitespace or `/`. Multiple repositories may be queued at once. Existing mirrors are reported but never overwritten automatically.

## Queue

{QUEUE_START}

{QUEUE_END}

## Last result

{RESULT_START}
{result_text}
{RESULT_END}
"""


def replace_block(text: str, start: str, end: str, content: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{content.rstrip()}\n{end}"
    if not pattern.search(text):
        raise ValueError(f"missing control block {start}")
    return pattern.sub(replacement, text, count=1)


def queue_lines(body: str) -> list[str]:
    pattern = re.compile(re.escape(QUEUE_START) + r"(.*?)" + re.escape(QUEUE_END), re.DOTALL)
    match = pattern.search(body)
    if not match:
        raise ValueError("Release body is missing the mirror queue block")
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def extract_url(line: str) -> str:
    markdown = MARKDOWN_LINK_RE.search(line)
    matches = [markdown.group(1)] if markdown else URL_RE.findall(line.replace("\u00a0", " "))
    if len(matches) != 1:
        raise ValueError("queue line must contain exactly one HTTPS repository URL")
    return matches[0]


def normalize_source_url(value: str) -> str:
    value = value.replace("\u00a0", " ").strip()
    parsed = urlparse(value)
    if parsed.query or parsed.fragment:
        raise ValueError("repository URL must not contain query or fragment components")
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    normalized = urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", "", ""))
    validate_source_url(normalized)
    parsed = urlparse(normalized)
    if parsed.hostname and parsed.hostname.lower() == "github.com":
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 2:
            raise ValueError("GitHub source URL must identify exactly one owner/repository")
    return normalized


def github_api_json(url: str, token: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "web-ingest-git-mirror",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def source_info(source_url: str, token: str) -> SourceInfo:
    normalized = normalize_source_url(source_url)
    parsed = urlparse(normalized)
    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.hostname == "github.com":
        owner, repo = path_parts
        api = f"https://api.github.com/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
        payload = github_api_json(api, token)
        if payload.get("private") or payload.get("visibility") not in {None, "public"}:
            raise ValueError("private GitHub repositories are not allowed")
        web_url = str(payload.get("html_url") or normalized).rstrip("/")
        full_name = str(payload.get("full_name") or f"{owner}/{repo}")
        name = str(payload.get("name") or repo)
        description = payload.get("description")
        if description is not None:
            description = str(description).strip() or None
        return SourceInfo(
            clone_url=web_url,
            web_url=web_url,
            repository_name=name,
            source_label=full_name,
            description=description,
            destination=default_destination(web_url),
        )

    label = "/".join(path_parts)
    return SourceInfo(
        clone_url=normalized,
        web_url=normalized,
        repository_name=path_parts[-1],
        source_label=label,
        description=None,
        destination=default_destination(normalized),
    )


def markdown_text(value: str) -> str:
    return " ".join(value.split()).replace("|", r"\|")


def index_row(info: SourceInfo) -> str:
    description = markdown_text(info.description) if info.description else "—"
    return (
        f"| {markdown_text(info.repository_name)} | {description} | "
        f"[{markdown_text(info.source_label)}]({info.web_url}) | "
        f"[Mirror](data/{info.destination}/) |"
    )


def source_url_from_row(row: str) -> str | None:
    links = re.findall(r"\[[^\]]+\]\((https://[^)]+)\)", row)
    return normalize_source_url(links[0]) if links else None


def upsert_readme(readme: str, infos: list[SourceInfo]) -> str:
    pattern = re.compile(re.escape(INDEX_START) + r"(.*?)" + re.escape(INDEX_END), re.DOTALL)
    match = pattern.search(readme)
    if not match:
        raise ValueError("git-mirror README is missing mirror index markers")
    lines = [line for line in match.group(1).strip().splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("git-mirror README mirror table is malformed")
    header = lines[:2]
    rows: dict[str, str] = {}
    for row in lines[2:]:
        source = source_url_from_row(row)
        key = source.casefold() if source and urlparse(source).hostname == "github.com" else source
        if key:
            rows[key] = row
    for info in infos:
        source = normalize_source_url(info.web_url)
        key = source.casefold() if urlparse(source).hostname == "github.com" else source
        rows[key] = index_row(info)
    ordered = sorted(rows.values(), key=lambda row: row.split("|", 2)[1].strip().casefold())
    block = "\n".join([*header, *ordered])
    return pattern.sub(f"{INDEX_START}\n\n{block}\n\n{INDEX_END}", readme, count=1)


def enrich_source_metadata(info: SourceInfo) -> None:
    path = DATA_ROOT / info.destination / "source.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["upstream"] = {
        "repository_name": info.repository_name,
        "description": info.description,
        "web_url": info.web_url,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def process_release(body: str, token: str) -> list[RequestResult]:
    results: list[RequestResult] = []
    successful_infos: list[SourceInfo] = []
    seen: set[str] = set()

    for raw in queue_lines(body):
        try:
            candidate = normalize_source_url(extract_url(raw))
            dedupe_key = candidate.casefold() if urlparse(candidate).hostname == "github.com" else candidate
            if dedupe_key in seen:
                results.append(RequestResult(raw, candidate, candidate, "duplicate", "duplicate request ignored"))
                continue
            seen.add(dedupe_key)
            info = source_info(candidate, token)
            target = DATA_ROOT / info.destination
            if target.exists():
                results.append(RequestResult(raw, info.web_url, info.source_label, "already_mirrored", "already mirrored; existing snapshot kept"))
                continue

            try:
                import_snapshot(info.clone_url, destination=info.destination)
                collect_latest_release(info.web_url, destination=info.destination)
                enrich_source_metadata(info)
                validation_errors = validate_one(target / "source.json")
                if validation_errors:
                    raise RuntimeError("; ".join(validation_errors))
            except Exception:
                if target.exists():
                    shutil.rmtree(target)
                raise

            successful_infos.append(info)
            results.append(RequestResult(raw, info.web_url, info.source_label, "mirrored", "mirror created"))
        except Exception as exc:
            message = " ".join(str(exc).split())[:300] or type(exc).__name__
            results.append(RequestResult(raw, None, raw[:120], "failed", message))

    if successful_infos:
        README_PATH.write_text(
            upsert_readme(README_PATH.read_text(encoding="utf-8"), successful_infos),
            encoding="utf-8",
        )
    return results


def repository_api_base(repository: str) -> str:
    owner, name = repository.split("/", 1)
    return f"https://api.github.com/repos/{quote(owner, safe='')}/{quote(name, safe='')}"


def get_fixed_release(repository: str, token: str) -> dict:
    return github_api_json(f"{repository_api_base(repository)}/releases/tags/{RELEASE_TAG}", token)


def ensure_fixed_release(repository: str, token: str) -> dict:
    try:
        return get_fixed_release(repository, token)
    except HTTPError as exc:
        if exc.code != 404:
            raise
    return github_api_json(
        f"{repository_api_base(repository)}/releases",
        token,
        method="POST",
        payload={
            "tag_name": RELEASE_TAG,
            "target_commitish": "main",
            "name": RELEASE_TITLE,
            "body": release_body(),
            "draft": False,
            "prerelease": False,
        },
    )


def release_from_event(event_path: Path, repository: str, token: str) -> dict:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    release = event.get("release")
    if isinstance(release, dict) and release.get("tag_name") == RELEASE_TAG:
        return release
    return get_fixed_release(repository, token)


def write_result_file(path: Path, release: dict, results: list[RequestResult]) -> None:
    payload = {
        "release_id": release["id"],
        "results": [asdict(item) for item in results],
        "release_body": release_body(results),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def publish_result_file(path: Path, repository: str, token: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    github_api_json(
        f"{repository_api_base(repository)}/releases/{int(payload['release_id'])}",
        token,
        method="PATCH",
        payload={"body": payload["release_body"], "name": RELEASE_TITLE},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Release control plane for public Git repository mirrors")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ensure-release")

    process = sub.add_parser("process")
    process.add_argument("--event-path", type=Path, required=True)
    process.add_argument("--result-file", type=Path, required=True)

    publish = sub.add_parser("publish")
    publish.add_argument("--result-file", type=Path, required=True)

    args = parser.parse_args()
    repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repository or not token:
        parser.error("GITHUB_REPOSITORY and GITHUB_TOKEN are required")

    if args.command == "ensure-release":
        release = ensure_fixed_release(repository, token)
        print(f"{release.get('html_url', '')}")
        return 0
    if args.command == "process":
        release = release_from_event(args.event_path, repository, token)
        results = process_release(str(release.get("body") or ""), token)
        write_result_file(args.result_file, release, results)
        print(json.dumps([asdict(item) for item in results], ensure_ascii=False))
        return 0
    if args.command == "publish":
        publish_result_file(args.result_file, repository, token)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
