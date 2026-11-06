"""One fixed GitHub Issue for human login prompts; never publish credentials."""
from __future__ import annotations

import os

import controller

TITLE = "[Baidu Drive] Login required"
RELEASE_URL = "https://github.com/teddyli18000/web-ingest/releases/tag/baidu-drive-live"
GUIDE_URL = "https://github.com/teddyli18000/web-ingest/blob/main/baidu-drive/AUTHORIZATION.md"
BODY = (
    "@teddyli18000 The Baidu Drive bot requires renewed account authorization.\n\n"
    "Your current transfer is paused at its existing checkpoint; no completed bytes are lost.\n\n"
    f"Run the local browser-login helper described in [the guide]({GUIDE_URL}). "
    "It updates the private GitHub Secret via gh CLI and automatically wakes the same master scheduler.\n\n"
    f"Transfer control and status: [fixed Release]({RELEASE_URL}).\n\n"
    "Never post cookies, passwords or tokens in this Issue.\n"
)


def synchronize(gh: controller.GitHub) -> None:
    runtime, _ = gh.read_json(controller.RUNTIME_PATH, default=controller.DEFAULT_RUNTIME)
    task = controller.load_active_task(gh, runtime)
    if task is None:
        return
    needed = task.get("status") == "NEEDS_LOGIN"
    issues = gh.request("GET", gh.api + "/issues?state=all&per_page=100")
    matches = [item for item in issues if item.get("title") == TITLE and "pull_request" not in item]
    if len(matches) > 1:
        raise controller.ProtocolError("multiple Baidu Drive login Issues exist")
    issue = matches[0] if matches else None
    if needed and issue is None:
        gh.request("POST", gh.api + "/issues", obj={"title": TITLE, "body": BODY})
    elif needed and issue["state"] == "closed":
        gh.request("PATCH", gh.api + f"/issues/{issue['number']}", obj={"state": "open"})
        gh.request("POST", gh.api + f"/issues/{issue['number']}/comments", obj={"body": BODY})
    elif not needed and issue is not None and issue["state"] == "open":
        gh.request("PATCH", gh.api + f"/issues/{issue['number']}", obj={"state": "closed"})


def main() -> int:
    gh = controller.GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    synchronize(gh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
