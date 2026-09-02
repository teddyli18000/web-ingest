#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
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


def commit_label(commit: str) -> str:
    short = commit[:12]
    repository = os.environ.get("GITHUB_REPOSITORY")
    if repository:
        return f"[{short}](https://github.com/{repository}/commit/{commit})"
    return short


def main() -> int:
    parser = argparse.ArgumentParser(description="Observe direct-to-main temp-work boundary incidents.")
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    args = parser.parse_args()

    incidents: list[str] = []
    observed_workspaces: set[str] = set()

    for commit in commit_list(args.before, args.after):
        files = changed_files(commit)
        workspaces = sorted({ws for path in files if (ws := workspace_for(path))})
        if not workspaces:
            continue

        observed_workspaces.update(workspaces)
        label = commit_label(commit)

        if len(workspaces) > 1:
            incidents.append(
                f"{label}: one commit touched multiple temp workspaces: "
                + ", ".join(f"`temp-work/{workspace}/`" for workspace in workspaces)
            )
            continue

        workspace = workspaces[0]
        outside = [
            path
            for path in files
            if path not in ROOT_POLICY_FILES and not path.startswith(f"temp-work/{workspace}/")
        ]
        if outside:
            incidents.append(
                f"{label}: `temp-work/{workspace}/` work also touched paths outside that workspace: "
                + ", ".join(f"`{path}`" for path in outside)
            )

    print("## Temp-work patrol")
    print()
    print("Observational patrol only. Boundary incidents are recorded here and do not fail the run.")

    if observed_workspaces:
        print("\nObserved workspaces:")
        for workspace in sorted(observed_workspaces):
            print(f"- `temp-work/{workspace}/`")
    else:
        print("\nNo temporary workspace content changed.")

    if incidents:
        print("\n### Recorded boundary incidents")
        for incident in incidents:
            print(f"- {incident}")
    else:
        print("\nNo boundary incidents recorded.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
