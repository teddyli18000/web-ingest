#!/usr/bin/env bash
# Dispatch one wave of temp-pdfcrack. No secret is echoed.
#
#   dispatch.sh <space> <start> <span> <attempt> [budget_seconds]
set -uo pipefail

space=${1:?space}
start=${2:?start}
span=${3:?span}
attempt=${4:?attempt}
budget=${5:-14400}

dispatch() {
  gh workflow run temp-pdfcrack.yml \
    --repo "${GITHUB_REPOSITORY}" \
    -f "space=${space}" \
    -f "start=${start}" \
    -f "span=${span}" \
    -f "budget_seconds=${budget}" \
    -f "attempt=${attempt}"
}

if message="$(dispatch 2>&1)"; then
  echo "dispatched space=${space} start=${start} span=${span} attempt=${attempt} (repository token)"
  exit 0
fi
echo "repository token refused to dispatch: ${message}"

if [ -n "${DISPATCH_TOKEN:-}" ] && message="$(GH_TOKEN="${DISPATCH_TOKEN}" dispatch 2>&1)"; then
  echo "dispatched space=${space} start=${start} span=${span} attempt=${attempt} (dispatch token)"
  exit 0
fi

echo "::error::could not dispatch a wave; the chain stopped here"
exit 1
