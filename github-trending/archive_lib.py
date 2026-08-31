from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REPO_RE = re.compile(r"^[^/\s]+/[^/\s]+$")
REPO_URL_RE = re.compile(r"https://github\.com/([^/\s]+)/([^)/\s#?]+)")


def to_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def normalize_repo(value: str) -> str | None:
    value = value.strip()
    if value.startswith("https://github.com/"):
        value = value[len("https://github.com/"):]
    value = value.strip("/").split("?", 1)[0].split("#", 1)[0]
    parts = value.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return None
    repo = f"{parts[0]}/{parts[1]}"
    return repo if REPO_RE.fullmatch(repo) else None


def make_item(rank: int, repo: str, *, language: str | None = None,
              stars_today: int | None = None, total_stars: int | None = None,
              forks: int | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"rank": rank, "repo": repo}
    if language:
        out["language"] = language
    if stars_today is not None:
        out["stars_today"] = stars_today
    if total_stars is not None:
        out["total_stars"] = total_stars
    if forks is not None:
        out["forks"] = forks
    return out


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    scope = snapshot.get("scope")
    items = snapshot.get("items")
    if not isinstance(scope, str) or not scope:
        raise ValueError("snapshot scope must be non-empty")
    if not isinstance(items, list) or not items:
        raise ValueError(f"snapshot {scope!r} has no items")
    seen: set[str] = set()
    for expected_rank, entry in enumerate(items, start=1):
        if entry.get("rank") != expected_rank:
            raise ValueError(f"snapshot {scope}: non-contiguous rank")
        repo = entry.get("repo")
        if not isinstance(repo, str) or normalize_repo(repo) != repo:
            raise ValueError(f"snapshot {scope}: invalid repo {repo!r}")
        key = repo.casefold()
        if key in seen:
            raise ValueError(f"snapshot {scope}: duplicate repo {repo}")
        seen.add(key)


def validate_day(day: dict[str, Any]) -> None:
    if day.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    date = day.get("date")
    if not isinstance(date, str) or not DATE_RE.fullmatch(date):
        raise ValueError(f"invalid date {date!r}")
    snapshots = day.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise ValueError(f"{date}: no snapshots")
    scopes: set[str] = set()
    for snapshot in snapshots:
        validate_snapshot(snapshot)
        scope = snapshot["scope"].casefold()
        if scope in scopes:
            raise ValueError(f"{date}: duplicate scope {scope}")
        scopes.add(scope)


def day_path(root: Path, date: str) -> Path:
    return root / "data" / date[:4] / date[5:7] / date[8:10] / "trending.json"


def write_day(root: Path, day: dict[str, Any]) -> Path:
    validate_day(day)
    path = day_path(root, day["date"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(day, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def read_day(path: Path) -> dict[str, Any]:
    day = json.loads(path.read_text(encoding="utf-8"))
    validate_day(day)
    return day


class TrendingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_article = False
        self.depth = 0
        self.current: dict[str, Any] | None = None
        self.capture_kind: str | None = None
        self.capture_tag: str | None = None
        self.text: list[str] = []
        self.results: list[dict[str, Any]] = []

    @staticmethod
    def attrs_map(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {k: (v or "") for k, v in attrs}

    def start_capture(self, kind: str, tag: str) -> None:
        self.capture_kind = kind
        self.capture_tag = tag
        self.text = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = self.attrs_map(attrs)
        classes = set(a.get("class", "").split())
        if not self.in_article:
            if tag == "article" and "Box-row" in classes:
                self.in_article = True
                self.depth = 1
                self.current = {"repo": None, "language": None, "stars_today": None,
                                "total_stars": None, "forks": None}
            return

        self.depth += 1
        if self.current is None:
            return

        if tag == "a":
            href = a.get("href", "")
            if self.current["repo"] is None and href.startswith("/") and href.count("/") == 2:
                repo = normalize_repo(href)
                if repo:
                    self.current["repo"] = repo
            if href.endswith("/stargazers"):
                self.start_capture("total_stars", "a")
            elif href.endswith("/forks") or href.endswith("/network/members"):
                self.start_capture("forks", "a")
        elif tag == "span" and a.get("itemprop") == "programmingLanguage":
            self.start_capture("language", "span")
        elif tag == "span" and "float-sm-right" in classes:
            self.start_capture("stars_today", "span")

    def handle_data(self, data: str) -> None:
        if self.capture_kind:
            self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_article:
            return

        if self.capture_kind and tag == self.capture_tag and self.current is not None:
            text = " ".join("".join(self.text).split())
            kind = self.capture_kind
            if kind == "language":
                self.current[kind] = text or None
            elif kind == "stars_today":
                match = re.search(r"([\d,]+)\s+stars?\s+today", text, re.I)
                self.current[kind] = to_int(match.group(1)) if match else None
            else:
                match = re.search(r"[\d,]+", text)
                self.current[kind] = to_int(match.group(0)) if match else None
            self.capture_kind = None
            self.capture_tag = None
            self.text = []

        self.depth -= 1
        if tag == "article" and self.depth <= 0:
            if self.current and self.current.get("repo"):
                self.results.append(self.current)
            self.in_article = False
            self.depth = 0
            self.current = None
            self.capture_kind = None
            self.capture_tag = None
            self.text = []


def parse_trending_html(html: str) -> list[dict[str, Any]]:
    parser = TrendingHTMLParser()
    parser.feed(html)
    items: list[dict[str, Any]] = []
    for rank, raw in enumerate(parser.results, start=1):
        items.append(make_item(rank, raw["repo"], language=raw.get("language"),
                               stars_today=raw.get("stars_today"),
                               total_stars=raw.get("total_stars"), forks=raw.get("forks")))
    if not items:
        raise ValueError("no GitHub Trending repository cards found")
    validate_snapshot({"scope": "all", "items": items})
    return items


def parse_markdown_language_archive(text: str) -> dict[str, list[dict[str, Any]]]:
    scopes: dict[str, list[dict[str, Any]]] = {}
    scope: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("####"):
            name = line[4:].strip()
            if name:
                scope = name.casefold().replace(" ", "-")
                scopes.setdefault(scope, [])
            continue
        if not scope or not line.startswith("*"):
            continue
        match = REPO_URL_RE.search(line)
        if not match:
            continue
        repo = normalize_repo(f"{match.group(1)}/{match.group(2)}")
        if not repo:
            continue
        entries = scopes[scope]
        if any(x["repo"].casefold() == repo.casefold() for x in entries):
            continue
        entries.append(make_item(len(entries) + 1, repo))
    return {scope: items for scope, items in scopes.items() if items}


def merge_candidate(store: dict[str, dict[str, tuple[int, dict[str, Any]]]], date: str,
                    scope: str, score: int, snapshot: dict[str, Any]) -> bool:
    validate_snapshot(snapshot)
    existing = store.setdefault(date, {}).get(scope)
    if existing is None or score > existing[0]:
        store[date][scope] = (score, snapshot)
        return True
    return False
