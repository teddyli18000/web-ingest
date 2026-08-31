#!/usr/bin/env python3
from __future__ import annotations

import sys

from archive_lib import iter_archive_files, read_json, validate_document


def main() -> int:
    files = iter_archive_files()
    errors: list[str] = []
    for path in files:
        payload = read_json(path)
        day = path.parent.name
        month = path.parent.parent.name
        year = path.parent.parent.parent.name
        expected_date = f"{year}-{month}-{day}"
        for item in validate_document(payload, expected_date):
            errors.append(f"{path}: {item}")

    if errors:
        print("Google Trending archive validation failed:")
        for item in errors:
            print(f"- {item}")
        return 1

    print(f"Google Trending archive validation passed ({len(files)} daily files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
