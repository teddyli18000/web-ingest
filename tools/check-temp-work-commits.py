#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = "temp-work/"
ROOT_POLICY_FILES = {"temp-work/README.md", "temp-work/AGENTS.md"}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def commit_list(before: str, after: str) -> list[str]:
    if not before or set(before) == {"0"}:
        return [after]
    return [line for line in git("rev-list", "--reverse", f"{before}..{after}").splitlines() if line]


def changed_files(commit: str) -> list[str]:
    return [
        line
        for line in git("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit).splitlines()
        if line
    ]


def workspace_for(path: str) -> str | None:
    if not path.startswith(TEMP_ROOT) or path in ROOT_POLICY_FILES:
        return None
    rest = path[len(TEMP_ROOT) :]
    if "/" not in rest:
        return None
    return rest.split("/", 1)[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Patrol direct-to-main temp-work commits.")
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    args = parser.parse_args()

    violations: list[str] = []
    notices: list[str] = []
    touched_counts: dict[str, int] = defaultdict(int)

    for commit in commit_list(args.before, args.after):
        files = changed_files(commit)
        workspaces = sorted({ws for path in files if (ws := workspace_for(path))})
        if not workspaces:
            continue

        short = commit[:12]
        if len(workspaces) > 1:
            violations.append(
                f"{short}: one commit touched multiple temp workspaces: {', '.join(workspaces)}"
            )
            continue

        workspace = workspaces[0]
        touched_counts[workspace] += 1
        outside = [
            path
            for path in files
            if path not in ROOT_POLICY_FILES and not path.startswith(f"temp-work/{workspace}/")
        ]
        if outside:
            notices.append(
                f"{short}: workspace {workspace} also touched paths outside its workspace: "
                + ", ".join(outside)
            )

        readme = ROOT / "temp-work" / workspace / "README.md"
        if not readme.is_file() or not readme.read_text(encoding="utf-8").strip():
            violations.append(f"{short}: temp-work/{workspace}/ is missing a non-empty README.md")

    for workspace, count in sorted(touched_counts.items()):
        if count >= 4:
            notices.append(
                f"high activity: {count} commits in this push touched temp-work/{workspace}/; "
                "writers should re-read latest main immediately before every write and retry on stale-SHA conflicts"
            )

    print("## Temp-work patrol")
    print()
    if touched_counts:
        print("Workspaces in this push:")
        for workspace, count in sorted(touched_counts.items()):
            print(f"- temp-work/{workspace}/: {count} commit(s)")
    else:
        print("No temporary workspace content changed.")

    if notices:
        print("\nNotices:")
        for item in notices:
            print(f"- {item}")

    if violations:
        print("\nViolations:")
        for item in violations:
            print(f"- {item}")
        return 1

    print("\nPatrol passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
