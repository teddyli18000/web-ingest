name: Git mirror - {{LABEL}}

on:
  push:
    branches:
      - main
    paths:
      - {{WORKFLOW_PATH_JSON}}
  workflow_dispatch:

permissions:
  contents: write

env:
  SOURCE_URL: {{SOURCE_URL_JSON}}
  SOURCE_BRANCH: {{SOURCE_BRANCH_JSON}}
  MIRROR_DESTINATION: {{DESTINATION_JSON}}
  WORKFLOW_PATH: {{WORKFLOW_PATH_JSON}}

concurrency:
  group: git-mirror-{{SLUG}}
  cancel-in-progress: false

jobs:
  mirror:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Validate git-mirror task
        run: |
          python3 -m py_compile git-mirror/*.py
          python3 -m unittest discover -s git-mirror/tests -v
          python3 git-mirror/validate_snapshots.py

      - name: Import public Git snapshot
        shell: bash
        run: |
          set -euo pipefail
          args=(--source-url "$SOURCE_URL")
          if [ -n "$SOURCE_BRANCH" ]; then
            args+=(--branch "$SOURCE_BRANCH")
          fi
          if [ -n "$MIRROR_DESTINATION" ]; then
            args+=(--destination "$MIRROR_DESTINATION")
          fi
          python3 git-mirror/import_snapshot.py "${args[@]}"

      - name: Validate imported snapshot
        run: python3 git-mirror/validate_snapshots.py

      - name: Commit snapshot and self-clean
        shell: bash
        run: |
          set -euo pipefail
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add git-mirror/data
          git rm -- "$WORKFLOW_PATH"

          git commit -m "data(git-mirror): import {{LABEL}} snapshot"
          git pull --rebase origin main
          git push origin HEAD:main
