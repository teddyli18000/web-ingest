#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

import backfill
from scope_normalization import normalize_scope

_original_build_output = backfill.build_output


def normalize_store(store: dict[str, dict[str, tuple[int, dict[str, Any]]]]) -> dict[str, dict[str, tuple[int, dict[str, Any]]]]:
    """Canonicalize backfill scope keys before files or manifest are written."""
    normalized: dict[str, dict[str, tuple[int, dict[str, Any]]]] = {}
    for date, scopes in store.items():
        day = normalized.setdefault(date, {})
        for raw_scope, (score, original) in scopes.items():
            scope = normalize_scope(raw_scope)
            candidate = dict(original)
            candidate["scope"] = scope
            current = day.get(scope)
            if current is None or score > current[0]:
                day[scope] = (score, candidate)
    return normalized


def canonical_build_output(store, output, stats):
    return _original_build_output(normalize_store(store), output, stats)


def main() -> int:
    # The low-level source converter stays untouched; this wrapper guarantees
    # canonical scopes for every deliberate future rebuild/backfill.
    backfill.build_output = canonical_build_output
    return backfill.main()


if __name__ == "__main__":
    raise SystemExit(main())
