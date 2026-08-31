#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
LOCAL_TZ = ZoneInfo("Asia/Singapore")
POST_RUN_BUFFER_MINUTES = 15
REFERENCE_YEAR = 2028  # leap year: exercises every month/day shape in one pass

CRON_RE = re.compile(r"^\s*-\s*cron:\s*['\"]([^'\"]+)['\"]\s*(?:#.*)?$", re.MULTILINE)
TIMEOUT_RE = re.compile(r"^\s*timeout-minutes:\s*(\d+)\s*(?:#.*)?$", re.MULTILINE)
WORKFLOW_DISPATCH_RE = re.compile(r"^\s{2}workflow_dispatch\s*:\s*(?:#.*)?$", re.MULTILINE)
TOP_LEVEL_CONCURRENCY_RE = re.compile(r"^concurrency\s*:\s*(?:#.*)?$", re.MULTILINE)
TEMPORARY_NAME_PARTS = ("backfill", "repair", "migration", "probe", "diagnostic", "temp")


@dataclass(frozen=True)
class WorkflowSchedule:
    name: str
    path: Path
    crons: tuple[str, ...]
    timeout_minutes: int


@dataclass(frozen=True)
class RunWindow:
    workflow: str
    cron: str
    start: datetime
    busy_until: datetime
    reserved_until: datetime


errors: list[str] = []


def error(message: str) -> None:
    errors.append(message)


def split_piece(piece: str, low: int, high: int, *, dow: bool = False) -> set[int]:
    step = 1
    base = piece
    if "/" in piece:
        base, step_text = piece.split("/", 1)
        if not step_text.isdigit() or int(step_text) <= 0:
            raise ValueError(f"invalid step: {piece}")
        step = int(step_text)

    if base == "*":
        start, end = low, high
    elif "-" in base:
        start_text, end_text = base.split("-", 1)
        if not start_text.isdigit() or not end_text.isdigit():
            raise ValueError(f"invalid range: {piece}")
        start, end = int(start_text), int(end_text)
    else:
        if not base.isdigit():
            raise ValueError(f"unsupported cron token: {piece}")
        value = int(base)
        if dow and value == 7:
            value = 0
        if not low <= value <= high:
            raise ValueError(f"cron value out of range: {piece}")
        return {value}

    if start > end or start < low or end > high:
        raise ValueError(f"cron range out of bounds: {piece}")
    values = set(range(start, end + 1, step))
    if dow and 7 in values:
        values.remove(7)
        values.add(0)
    return values


def expand_field(field: str, low: int, high: int, *, dow: bool = False) -> set[int]:
    values: set[int] = set()
    for piece in field.split(","):
        piece = piece.strip()
        if not piece:
            raise ValueError(f"empty cron field component: {field}")
        values.update(split_piece(piece, low, high, dow=dow))
    return values


def cron_events(expr: str, year: int = REFERENCE_YEAR) -> list[datetime]:
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(f"expected five cron fields, got {len(parts)}: {expr}")
    minute_field, hour_field, dom_field, month_field, dow_field = parts
    minutes = expand_field(minute_field, 0, 59)
    hours = expand_field(hour_field, 0, 23)
    doms = expand_field(dom_field, 1, 31)
    months = expand_field(month_field, 1, 12)
    dows = expand_field(dow_field, 0, 7, dow=True)
    dom_wild = dom_field == "*"
    dow_wild = dow_field == "*"

    current = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    events: list[datetime] = []
    while current < end:
        cron_dow = (current.weekday() + 1) % 7  # Python Monday=0; cron Sunday=0
        dom_match = current.day in doms
        dow_match = cron_dow in dows
        if dom_wild and dow_wild:
            day_match = True
        elif dom_wild:
            day_match = dow_match
        elif dow_wild:
            day_match = dom_match
        else:
            # POSIX/Vixie cron: restricted DOM and DOW are ORed.
            day_match = dom_match or dow_match

        if current.month in months and day_match:
            for hour in sorted(hours):
                for minute in sorted(minutes):
                    events.append(current.replace(hour=hour, minute=minute))
        current += timedelta(days=1)
    return events


def discover_schedules() -> list[WorkflowSchedule]:
    schedules: list[WorkflowSchedule] = []
    if not WORKFLOW_DIR.is_dir():
        error("missing .github/workflows directory")
        return schedules

    for path in sorted(WORKFLOW_DIR.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        crons = tuple(CRON_RE.findall(text))
        if not crons:
            continue

        if any(part in path.stem.casefold() for part in TEMPORARY_NAME_PARTS):
            error(f"temporary workflow must not be scheduled: {path.relative_to(ROOT)}")
        if not WORKFLOW_DISPATCH_RE.search(text):
            error(f"scheduled workflow lacks workflow_dispatch: {path.relative_to(ROOT)}")
        if not TOP_LEVEL_CONCURRENCY_RE.search(text):
            error(f"scheduled workflow lacks top-level concurrency: {path.relative_to(ROOT)}")

        timeout_values = [int(value) for value in TIMEOUT_RE.findall(text)]
        if not timeout_values:
            error(f"scheduled workflow lacks timeout-minutes: {path.relative_to(ROOT)}")
            continue
        timeout = max(timeout_values)
        if timeout <= 0:
            error(f"scheduled workflow has invalid timeout: {path.relative_to(ROOT)}")
            continue

        task_readme = ROOT / path.stem / "README.md"
        if not task_readme.is_file():
            error(f"scheduled task lacks task README: {path.stem}/README.md")

        for expr in crons:
            try:
                cron_events(expr)
            except ValueError as exc:
                error(f"unsupported cron in {path.name}: {expr!r}: {exc}")

        schedules.append(WorkflowSchedule(path.name, path, crons, timeout))
    return schedules


def build_windows(schedules: list[WorkflowSchedule]) -> list[RunWindow]:
    windows: list[RunWindow] = []
    for schedule in schedules:
        for expr in schedule.crons:
            try:
                starts = cron_events(expr)
            except ValueError:
                continue
            for start in starts:
                busy_until = start + timedelta(minutes=schedule.timeout_minutes)
                reserved_until = busy_until + timedelta(minutes=POST_RUN_BUFFER_MINUTES)
                windows.append(RunWindow(schedule.name, expr, start, busy_until, reserved_until))
    return sorted(windows, key=lambda item: (item.start, item.workflow, item.cron))


def check_load_balance(schedules: list[WorkflowSchedule]) -> None:
    windows = build_windows(schedules)
    reported: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    for index, left in enumerate(windows):
        for right in windows[index + 1 :]:
            if right.start >= left.reserved_until:
                break
            if left.workflow == right.workflow:
                continue

            pair = tuple(sorted(((left.workflow, left.cron), (right.workflow, right.cron))))
            if pair in reported:
                continue
            reported.add(pair)

            left_local = left.start.astimezone(LOCAL_TZ)
            right_local = right.start.astimezone(LOCAL_TZ)
            reserved_local = left.reserved_until.astimezone(LOCAL_TZ)
            error(
                "scheduled workload overlap: "
                f"{left.workflow} ({left.cron}) starts {left_local:%Y-%m-%d %H:%M} local and reserves through "
                f"{reserved_local:%H:%M}; {right.workflow} ({right.cron}) starts {right_local:%H:%M}"
            )


def check_repository_docs() -> None:
    required = [
        "README.md",
        "AGENTS.md",
        "tools/README.md",
        "tools/AGENTS.md",
        ".github/workflows/README.md",
        ".github/workflows/AGENTS.md",
    ]
    for relative in required:
        if not (ROOT / relative).is_file():
            error(f"missing repository maintenance file: {relative}")


def show_schedule(schedules: list[WorkflowSchedule]) -> None:
    print(f"Schedule policy: timeout + {POST_RUN_BUFFER_MINUTES} min cross-workflow buffer")
    print("Timezone for display: Asia/Singapore (cron remains UTC)")
    for schedule in schedules:
        print(f"\n{schedule.name} — timeout {schedule.timeout_minutes} min")
        for expr in schedule.crons:
            starts = cron_events(expr)
            sample_date = starts[0].astimezone(LOCAL_TZ).date() if starts else None
            sample_times = []
            if sample_date is not None:
                for start in starts:
                    local = start.astimezone(LOCAL_TZ)
                    if local.date() == sample_date:
                        sample_times.append(local.strftime("%H:%M"))
            local_summary = ", ".join(sample_times[:12]) or "n/a"
            print(f"  {expr:<20} local sample: {local_summary}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate web-ingest repository rules and Action schedule load.")
    parser.add_argument("--show", action="store_true", help="print the current scheduled workflow plan")
    args = parser.parse_args()

    check_repository_docs()
    schedules = discover_schedules()
    check_load_balance(schedules)

    if args.show:
        show_schedule(schedules)

    if errors:
        print("\nRepository integrity check failed:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("\nRepository integrity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
