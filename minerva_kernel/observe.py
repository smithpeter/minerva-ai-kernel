from __future__ import annotations

import json
import platform
import shlex
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .redaction import RedactionSummary
from .types import Decision, Observation, PolicyDecision


DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_TAIL_CHARS = 12000


def observe_command(
    command: Sequence[str],
    *,
    cwd: str | Path | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    tail_chars: int = DEFAULT_TAIL_CHARS,
) -> Observation:
    argv = [str(part) for part in command]
    if not argv:
        raise ValueError("observe requires a command after --")
    if timeout_seconds <= 0:
        raise ValueError("timeout must be greater than zero")
    if tail_chars <= 0:
        raise ValueError("tail_chars must be greater than zero")

    cwd_path = Path(cwd) if cwd is not None else Path.cwd()
    cwd_text = str(cwd_path.resolve())
    command_text = shlex.join(argv)
    started = time.monotonic()

    stdout = ""
    stderr = ""
    exit_code: int | None = None
    timed_out = False
    command_found = True
    error_type: str | None = None

    try:
        completed = subprocess.run(
            argv,
            cwd=cwd_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        exit_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        error_type = exc.__class__.__name__
        stdout = _coerce_output(exc.stdout)
        stderr = _append_line(
            _coerce_output(exc.stderr),
            f"Command timed out after {timeout_seconds:g} seconds",
        )
        exit_code = 124
    except FileNotFoundError as exc:
        command_found = False
        error_type = exc.__class__.__name__
        stderr = f"command not found: {argv[0]} ({exc.strerror or exc})"
        exit_code = 127
    except PermissionError as exc:
        error_type = exc.__class__.__name__
        stderr = f"permission denied: {argv[0]} ({exc.strerror or exc})"
        exit_code = 126

    duration_ms = max(0, int(round((time.monotonic() - started) * 1000)))
    stdout_tail = _tail(stdout, tail_chars)
    stderr_tail = _tail(stderr, tail_chars)

    runtime: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.system().lower() or sys.platform,
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "network_status": "unknown",
        "timeout_seconds": timeout_seconds,
        "tail_chars": tail_chars,
        "stdout_truncated": len(stdout) > tail_chars,
        "stderr_truncated": len(stderr) > tail_chars,
        "timed_out": timed_out,
        "command_found": command_found,
    }
    if error_type:
        runtime["error_type"] = error_type

    return Observation(
        command=command_text,
        cwd=cwd_text,
        exit_code=exit_code,
        stdout_tail=stdout_tail,
        stderr_tail=stderr_tail,
        duration_ms=duration_ms,
        source="local_shell",
        policy_summary=(
            f"command attempted with {timeout_seconds:g}s timeout; "
            f"stdout/stderr tails limited to {tail_chars} chars"
        ),
        runtime=runtime,
    )


def save_run_record(
    *,
    observation: Observation,
    decision: Decision,
    policy_decision: PolicyDecision,
    redactions: RedactionSummary | None,
    root: str | Path | None = None,
) -> Path:
    root_path = Path(root) if root is not None else Path.cwd()
    runs_dir = root_path / ".minerva" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    created_at = _utc_timestamp()
    path = runs_dir / f"{created_at}-{uuid.uuid4().hex[:8]}.json"
    record = build_run_record(
        created_at=created_at,
        observation=observation,
        decision=decision,
        policy_decision=policy_decision,
        redactions=redactions,
    )
    path.write_text(
        json.dumps(record, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def build_run_record(
    *,
    created_at: str,
    observation: Observation,
    decision: Decision,
    policy_decision: PolicyDecision,
    redactions: RedactionSummary | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": "run.v0",
        "created_at": created_at,
        "observation": observation.to_dict(),
        "decision": decision.to_dict(),
        "policy_decision": {
            "allowed": policy_decision.allowed,
            "reason": policy_decision.reason,
        },
    }
    if redactions and redactions.count:
        record["redactions"] = redactions.to_dict()
    return record


def _tail(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _append_line(text: str, line: str) -> str:
    if not text:
        return line
    return f"{text.rstrip()}\n{line}"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
