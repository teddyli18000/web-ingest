#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter, defaultdict
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


def recent_workspace_activity(workspace: str) -> tuple[int, list[tuple[str, int]]]:
    path = f"temp-work/{workspace}"
    commits = [
        line
        for line in git("log", "--since=5 minutes ago", "--format=%H", "--", path).splitlines()
        if line
    ]
    paths = [
        line
        for line in git("log", "--since=5 minutes ago", "--format=", "--name-only", "--", path).splitlines()
        if line
    ]
    hot_files = [(name, count) for name, count in Counter(paths).most_common() if count >= 3]
    return len(commits), hot_files


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

    for workspace in sorted(touched_counts):
        recent_count, hot_files = recent_workspace_activity(workspace)
        if recent_count >= 4:
            notices.append(
                f"high activity: {recent_count} commits in the last 5 minutes touched temp-work/{workspace}/; "
                "the patrol bot is tracking this workspace for contention"
            )
        for path, count in hot_files:
            notices.append(
                f"hot file: {path} changed {count} times in the last 5 minutes; "
                "prefer independent files for concurrent work when practical"
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
