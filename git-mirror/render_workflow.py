#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from import_snapshot import default_destination, destination_path, validate_source_url

TASK_ROOT = Path(__file__).resolve().parent
TEMPLATE = TASK_ROOT / "templates" / "one-shot-workflow.yml.tpl"


def workflow_slug(source_url: str, destination: str | None = None) -> str:
    key = destination or default_destination(source_url)
    name = Path(key).name.lower()
    name = re.sub(r"[^a-z0-9-]+", "-", name).strip("-") or "repo"
    digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:8]
    return f"{name[:40]}-{digest}"


def render(source_url: str, *, branch: str | None = None, destination: str | None = None, workflow_path: str | None = None) -> tuple[str, str]:
    validate_source_url(source_url)
    if destination:
        destination_path(destination)
    slug = workflow_slug(source_url, destination)
    label = slug
    workflow_path = workflow_path or f".github/workflows/git-mirror-{slug}.yml"
    if not workflow_path.startswith(".github/workflows/") or not workflow_path.endswith((".yml", ".yaml")):
        raise ValueError("workflow path must be a .yml/.yaml file under .github/workflows/")

    content = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "{{LABEL}}": label,
        "{{SLUG}}": slug,
        "{{SOURCE_URL_JSON}}": json.dumps(source_url),
        "{{SOURCE_BRANCH_JSON}}": json.dumps(branch or ""),
        "{{DESTINATION_JSON}}": json.dumps(destination or ""),
        "{{WORKFLOW_PATH_JSON}}": json.dumps(workflow_path),
    }
    for token, value in replacements.items():
        content = content.replace(token, value)
    unresolved = re.findall(r"\{\{[A-Z0-9_]+\}\}", content)
    if unresolved:
        raise ValueError(f"unresolved workflow template tokens: {sorted(set(unresolved))}")
    return workflow_path, content


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a one-shot public Git mirror workflow")
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--branch")
    parser.add_argument("--destination", help="relative path below git-mirror/data; omit for host/source-path default")
    parser.add_argument("--output", help="workflow path; defaults to .github/workflows/git-mirror-<slug>.yml")
    args = parser.parse_args()

    try:
        workflow_path, content = render(
            args.source_url,
            branch=args.branch,
            destination=args.destination,
            workflow_path=args.output,
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))

    if args.output:
        path = Path(workflow_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(workflow_path)
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
