#!/usr/bin/env bash
# Keep temp-pdfcrack alive across GitHub-side failures.
#
# A wave can fail without any shard failing: on 2026-11-11 one wave ended with
# "Internal server error. Correlation ID: ..." after all 20 shards had finished,
# which meant the advance job never ran and the chain died silently. This script
# looks at the finished wave and decides whether to advance, retry or stop.
set -euo pipefail

: "${GITHUB_REPOSITORY:?}"
: "${RUN_ID:?}"
: "${RUN_CONCLUSION:?}"
: "${RUN_TITLE:?}"

if [ "${RUN_CONCLUSION}" = "success" ]; then
  echo "wave ${RUN_ID} succeeded; the advance job already dispatched the next wave."
  exit 0
fi

parsed="$(sed -n 's/^pdfcrack s=\([0-9]*\) i=\([0-9]*\) p=\([0-9]*\) a=\([0-9]*\)$/\1 \2 \3 \4/p' <<<"${RUN_TITLE}")"
if [ -z "${parsed}" ]; then
  echo "no window in run title '${RUN_TITLE}'; not guessing."
  exit 0
fi
read -r space start span attempt <<<"${parsed}"

jobs="$(gh api "/repos/${GITHUB_REPOSITORY}/actions/runs/${RUN_ID}/jobs?per_page=100")"
failed="$(jq '[.jobs[] | select(.name|startswith("shard")) | select(.conclusion=="failure")] | length' <<<"${jobs}")"
ok="$(jq '[.jobs[] | select(.name|startswith("shard")) | select(.conclusion=="success")] | length' <<<"${jobs}")"
echo "wave ${RUN_ID}: conclusion=${RUN_CONCLUSION} space=${space} start=${start} shards_ok=${ok} shards_failed=${failed}"

{
  echo "## Watchdog"
  echo
  echo "- wave: \`${RUN_ID}\` — \`${RUN_CONCLUSION}\`"
  echo "- window: space \`${space}\` start \`${start}\` span \`${span}\` attempt \`${attempt}\`"
  echo "- shards: ${ok} ok, ${failed} failed"
} >> "${GITHUB_STEP_SUMMARY}"

if [ "${failed}" -gt 0 ]; then
  echo "a shard exited non-zero: either a hit (exit 42) or a hard failure. Chain stopped." | tee -a "${GITHUB_STEP_SUMMARY}"
  exit 0
fi

if [ "${ok}" -eq 20 ]; then
  out="$(python3 temp-work/pdfcrack/plan.py advance --space "${space}" --start "${start}" --span "${span}")"
  echo "${out}"
  next_space="$(sed -n 's/^next_space=//p' <<<"${out}")"
  next_start="$(sed -n 's/^next_start=//p' <<<"${out}")"
  next_span="$(sed -n 's/^next_span=//p' <<<"${out}")"
  stop="$(sed -n 's/^stop=//p' <<<"${out}")"
  if [ "${stop}" = "true" ]; then
    echo "plan exhausted" | tee -a "${GITHUB_STEP_SUMMARY}"
    exit 0
  fi
  bash temp-work/pdfcrack/dispatch.sh "${next_space}" "${next_start}" "${next_span}" 0
  exit 0
fi

if [ "${attempt}" -ge 3 ]; then
  echo "window retried ${attempt} times without finishing; stopping instead of guessing." | tee -a "${GITHUB_STEP_SUMMARY}"
  exit 0
fi

bash temp-work/pdfcrack/dispatch.sh "${space}" "${start}" "${span}" "$((attempt + 1))"
