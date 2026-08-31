from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote

# Only aliases whose meaning is unambiguous in the vetted historical sources.
_SCOPE_ALIASES = {
    "cpp": "c++",
}

# Keep this aligned with the deterministic historical backfill source ranking.
SOURCE_PRIORITY = {
    "Leko/github-trending-archive": 420,
    "antonkomarev/github-trending-archive": 380,
    "ifyour/github-trending-archive": 360,
    "larsbijl/trending_archive": 220,
    "hanishrao/trending-collection": 180,
}


def normalize_scope(value: str) -> str:
    """Return the canonical scope key used by this archive.

    Percent-encoded source slugs are decoded, case/whitespace is normalized,
    and a very small allowlist maps source-specific aliases to GitHub's
    display-style language name. Unknown scopes are preserved after the
    generic normalization instead of being guessed.
    """
    text = unquote(str(value)).strip().casefold()
    text = re.sub(r"\s+", "-", text)
    if not text:
        raise ValueError("scope must be non-empty")
    return _SCOPE_ALIASES.get(text, text)


def source_priority(snapshot: dict[str, Any]) -> int:
    return SOURCE_PRIORITY.get(str(snapshot.get("source", "")), 0)


def choose_snapshot(current: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Choose between two snapshots that normalize to the same date+scope.

    Historical source priority is the primary rule. Ties retain the current
    snapshot so the migration is deterministic and stable on rerun.
    """
    if source_priority(candidate) > source_priority(current):
        return candidate
    return current
