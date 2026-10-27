#!/usr/bin/env python3
"""Lease-bound file worker for direct Baidu Range -> Drive relay steps."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import os
import pathlib
import subprocess
import time
from typing import Any, Callable

import relay_control
import relay_state
import scheduler

MAX_STEP_OUTPUT_BYTES = 1 << 20
DEFAULT_RETRY_LIMIT = 3
DEFAULT_SESSION_RESTART_LIMIT = 2


class WorkerError(RuntimeError):
    pass


def public_error(kind: str) -> str:
    return {
        "auth": "Relay authentication is unavailable or expired.",
        "retryable": "Relay transport remained unavailable after bounded retries.",
        "session_expired": "Drive resumable session repeatedly expired.",
        "state": "Encrypted relay capability state could not be opened.",
        "input": "Relay worker input was rejected.",
        "zero_file_pending": "Zero-byte Drive creation path is not enabled yet.",
    }.get(kind, "Relay worker stopped safely.")


def restart_expired_session(
    record: dict[str, Any], lease_id: str, now: dt.datetime
) -> dict[str, Any]:
    """Discard only the expired Drive session and its session-scoped progress."""
    value = copy.deepcopy(record)
    relay_state.require_lease(value, lease_id)
    value["session_sealed"] = None
    value["confirmed_offset"] = 0
    value["hash_offset"] = 0
    value["md5_state"] = None
    value["computed_md5"] = None
    value["heartbeat_at"] = relay_state.now_iso(now)
    value["updated_at"] = value["heartbeat_at"]
    value["last_error"] = ""
    return value


def apply_step_output(
    record: dict[str, Any],
    lease_id: str,
    output: dict[str, Any],
    now: dt.datetime,
) -> dict[str, Any]:
    value = record
    relay_state.require_lease(value, lease_id)

    sealed = str(output.get("session_sealed") or "").strip()
    if sealed:
        existing = str(value.get("session_sealed") or "").strip()
        if not existing:
            value = relay_state.attach_session(value, lease_id, sealed, now)
        elif existing != sealed:
            raise WorkerError("relay step returned an unexpected replacement session")
    elif not str(value.get("session_sealed") or "").strip():
        raise WorkerError("relay step returned no resumable session")

    confirmed = int(output.get("confirmed_offset") or 0)
    hashed = int(output.get("hash_offset") or 0)
    current_confirmed = int(value.get("confirmed_offset") or 0)
    if confirmed < current_confirmed:
        # This record contains only Drive-confirmed offsets. A lower offset on
        # the same live session is not a valid reconciliation result.
        raise WorkerError(
            f"relay step tried to move confirmed offset backwards: {confirmed} < {current_confirmed}"
        )

    state_text = str(output.get("md5_state") or "").strip() or None
    computed = str(output.get("computed_md5") or "").strip() or None
    if confirmed != hashed:
        raise WorkerError("relay step returned misaligned Drive/hash offsets")
    current_hash = int(value.get("hash_offset") or 0)
    has_new_checkpoint = (
        confirmed != current_confirmed
        or hashed != current_hash
        or state_text != (str(value.get("md5_state") or "").strip() or None)
        or computed != (str(value.get("computed_md5") or "").strip() or None)
    )
    if has_new_checkpoint or output.get("complete"):
        value = relay_state.apply_relay_checkpoint(
            value,
            lease_id,
            confirmed,
            hashed,
            state_text,
            computed,
            now,
        )

    if bool(output.get("complete")):
        value = relay_state.complete(
            value,
            lease_id,
            str(output.get("drive_file_id") or ""),
            str(output.get("drive_md5") or ""),
            str(output.get("computed_md5") or ""),
            now,
        )
    return value


def run_worker_loop(
    repo: Any,
    task_id: str,
    file_id: str,
    lease_id: str,
    step: Callable[[dict[str, Any]], tuple[int, dict[str, Any]]],
    *,
    now_fn: Callable[[], dt.datetime] | None = None,
    monotonic_fn: Callable[[], float] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
    soft_runtime_seconds: int = scheduler.DEFAULT_SOFT_RUNTIME_SECONDS,
    retry_limit: int = DEFAULT_RETRY_LIMIT,
    session_restart_limit: int = DEFAULT_SESSION_RESTART_LIMIT,
) -> str:
    now_fn = now_fn or (lambda: dt.datetime.now(dt.timezone.utc))
    monotonic_fn = monotonic_fn or time.monotonic
    sleep_fn = sleep_fn or time.sleep
    started = monotonic_fn()
    consecutive_retryable = 0
    session_restarts = 0

    while True:
        record, _ = repo.read_record(task_id, file_id)
        if record is None:
            raise WorkerError("relay file state disappeared")
        relay_state.require_lease(record, lease_id)

        if monotonic_fn() - started >= soft_runtime_seconds:
            repo.mutate_record(
                task_id,
                file_id,
                lambda current: relay_state.pause(current, lease_id, now_fn(), "soft runtime boundary"),
                f"baidu-drive: pause relay file {file_id} at soft boundary",
            )
            return relay_state.PAUSED

        before_offset = int(record.get("confirmed_offset") or 0)
        returncode, output = step(record)
        if not isinstance(output, dict):
            raise WorkerError("relay step result is not an object")
        kind = str(output.get("error_kind") or "").strip()

        if kind == "session_expired":
            session_restarts += 1
            if session_restarts > session_restart_limit:
                repo.mutate_record(
                    task_id,
                    file_id,
                    lambda current: relay_state.fail(
                        current,
                        lease_id,
                        now_fn(),
                        public_error("session_expired"),
                        permanent=False,
                    ),
                    f"baidu-drive: stop repeatedly expired relay file {file_id}",
                )
                return relay_state.FAILED_RETRYABLE
            repo.mutate_record(
                task_id,
                file_id,
                lambda current: restart_expired_session(current, lease_id, now_fn()),
                f"baidu-drive: restart expired Drive session for {file_id}",
            )
            consecutive_retryable = 0
            continue

        # A command can fail before it has a trustworthy Drive reconciliation.
        # Only apply an output that carries the same/new session and does not
        # contradict an already persisted confirmed offset.
        sealed = str(output.get("session_sealed") or "").strip()
        candidate_offset = int(output.get("confirmed_offset") or 0)
        applied = False
        after_offset = before_offset
        if sealed and candidate_offset >= before_offset:
            updated = repo.mutate_record(
                task_id,
                file_id,
                lambda current: apply_step_output(current, lease_id, output, now_fn()),
                f"baidu-drive: checkpoint relay file {file_id}",
            )
            applied = True
            after_offset = int(updated.get("confirmed_offset") or 0)
            if updated.get("status") == relay_state.VERIFIED and returncode == 0:
                return relay_state.VERIFIED

        if returncode == 0 and not kind:
            if not applied:
                raise WorkerError("successful relay step returned no durable progress state")
            consecutive_retryable = 0
            continue

        if kind == "retryable" and after_offset > before_offset:
            consecutive_retryable = 0
            continue

        if kind == "retryable" and consecutive_retryable + 1 < retry_limit:
            consecutive_retryable += 1
            sleep_fn(float(1 << (consecutive_retryable - 1)))
            continue

        permanent = kind in {"state", "input", "zero_file_pending"}
        message = public_error(kind or "retryable")
        repo.mutate_record(
            task_id,
            file_id,
            lambda current: relay_state.fail(
                current,
                lease_id,
                now_fn(),
                message,
                permanent=permanent,
            ),
            f"baidu-drive: stop relay file {file_id}",
        )
        return relay_state.FAILED_PERMANENT if permanent else relay_state.FAILED_RETRYABLE


def subprocess_step(record: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    binary = os.environ.get("BAIDU_DRIVE_RELAY_BIN", "").strip()
    cookie = os.environ.get("BAIDU_DRIVE_BAIDU_AUTH_FILE", "").strip()
    token = os.environ.get("BAIDU_DRIVE_GOOGLE_ACCESS_TOKEN_FILE", "").strip()
    key = os.environ.get("BAIDU_DRIVE_STATE_KEY_FILE", "").strip()
    if not all((binary, cookie, token, key)):
        raise WorkerError("relay runtime authentication inputs are not configured")

    base = pathlib.Path(os.environ.get("RUNNER_TEMP") or ".") / "baidu-drive-relay"
    base.mkdir(parents=True, exist_ok=True)
    input_path = base / "input.json"
    output_path = base / "output.json"
    input_path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(input_path, 0o600)
    try:
        output_path.unlink()
    except FileNotFoundError:
        pass

    completed = subprocess.run(
        [
            binary,
            "--input-json", str(input_path),
            "--output-json", str(output_path),
            "--baidu-cookie-file", cookie,
            "--drive-access-token-file", token,
            "--state-key-file", key,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if not output_path.is_file():
        return completed.returncode or 1, {"error_kind": "retryable"}
    if output_path.stat().st_size > MAX_STEP_OUTPUT_BYTES:
        raise WorkerError("relay step output is too large")
    try:
        value = json.loads(output_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise WorkerError(f"relay step output is invalid: {exc}") from None
    if not isinstance(value, dict):
        raise WorkerError("relay step output is not an object")
    # The Go command may include a diagnostic message in its runner-local JSON.
    # Never copy that free-form message into Git/public logs; state uses only the
    # fixed public_error() strings above.
    value.pop("message", None)
    return completed.returncode, value


def write_status_output(status: str) -> None:
    output = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not output:
        return
    with open(output, "a", encoding="utf-8") as handle:
        print(f"relay_status={status}", file=handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--file-id", required=True)
    parser.add_argument("--lease-id", required=True)
    args = parser.parse_args(argv)

    repo = relay_control.GitHubRepo(
        os.environ.get("GITHUB_REPOSITORY", ""),
        os.environ.get("GITHUB_TOKEN", ""),
    )
    status = run_worker_loop(repo, args.task_id, args.file_id, args.lease_id, subprocess_step)
    write_status_output(status)
    print(f"relay worker stopped in {status}")
    return 0 if status in {relay_state.VERIFIED, relay_state.PAUSED} else 1


if __name__ == "__main__":
    raise SystemExit(main())
