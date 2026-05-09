from __future__ import annotations

import os
import re
import shlex
import shutil
import time
from pathlib import Path

from .policy import validate_action
from .types import Decision, Observation


DEFAULT_TAIL_CHARS = 4000
SENSITIVE_PATH_PARTS = frozenset(
    {
        ".aws",
        ".env",
        ".git-credentials",
        ".netrc",
        ".ssh",
        "authorized_keys",
        "credential",
        "credentials",
        "id_ed25519",
        "id_rsa",
        "private_key",
        "secret",
        "token",
    }
)


def execute_action(
    action: Decision,
    cwd: str | Path,
    observation: Observation | None = None,
) -> Observation:
    """Execute an explicitly requested read-only diagnostic action.

    The executor never runs model-provided shell commands and never writes files.
    It only inspects local metadata with standard-library APIs after the policy
    gate allows the decision.
    """

    started = time.monotonic()
    cwd_path = Path(cwd).resolve()
    policy_decision = validate_action(action)
    if not policy_decision.allowed:
        return _observation(
            action=action,
            cwd=cwd_path,
            stderr=f"policy blocked executor action: {policy_decision.reason}",
            duration_ms=_elapsed_ms(started),
            runtime={"policy_allowed": False, "policy_reason": policy_decision.reason},
        )

    if action.action == "stop":
        return _observation(
            action=action,
            cwd=cwd_path,
            stdout="no executor follow-up needed",
            duration_ms=_elapsed_ms(started),
            runtime={"policy_allowed": True, "executor_state": "stopped"},
        )

    if action.action == "check_command_exists":
        return _check_command_exists(action, cwd_path, observation, started)

    if action.action == "inspect_dependencies":
        return _inspect_dependencies(action, cwd_path, started)

    if action.action == "check_permissions":
        return _check_permissions(action, cwd_path, observation, started)

    if action.action == "check_logs":
        return _check_logs(action, cwd_path, observation, started)

    return Observation(
        command=f"executor:{action.action}",
        cwd=str(cwd_path),
        exit_code=None,
        stdout_tail=(
            f"read-only executor has no deterministic handler for {action.action}"
        ),
        stderr_tail="",
        duration_ms=_elapsed_ms(started),
        source="kernel_executor",
        policy_summary="explicit read-only executor; no shell commands or writes",
        runtime={
            "policy_allowed": True,
            "executor_state": "no_handler",
            "action": action.action,
        },
    )


def _check_command_exists(
    action: Decision,
    cwd: Path,
    observation: Observation | None,
    started: float,
) -> Observation:
    command = _candidate_command(observation)
    if not command:
        return _observation(
            action=action,
            cwd=cwd,
            stderr="no command candidate found in observation",
            duration_ms=_elapsed_ms(started),
            runtime={"policy_allowed": True, "executor_state": "missing_target"},
        )

    resolved = shutil.which(command)
    if resolved:
        stdout = f"command found: {command} -> {resolved}"
        exit_code = 0
    else:
        stdout = f"command not found on PATH: {command}"
        exit_code = 1

    return _observation(
        action=action,
        cwd=cwd,
        exit_code=exit_code,
        stdout=stdout,
        duration_ms=_elapsed_ms(started),
        runtime={
            "policy_allowed": True,
            "executor_state": "completed",
            "checked_command": command,
            "found": bool(resolved),
        },
    )


def _inspect_dependencies(action: Decision, cwd: Path, started: float) -> Observation:
    names = (
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        "setup.py",
        "setup.cfg",
        "package.json",
        "pnpm-lock.yaml",
        "package-lock.json",
        "uv.lock",
        "poetry.lock",
    )
    found: list[str] = []
    missing: list[str] = []
    for name in names:
        path = cwd / name
        if path.is_file():
            found.append(f"{name} ({path.stat().st_size} bytes)")
        else:
            missing.append(name)

    lines = ["dependency metadata files:"]
    lines.extend(f"- found: {item}" for item in found)
    if not found:
        lines.append("- found: none")
    lines.append("missing checked files: " + ", ".join(missing))

    return _observation(
        action=action,
        cwd=cwd,
        exit_code=0 if found else 1,
        stdout="\n".join(lines),
        duration_ms=_elapsed_ms(started),
        runtime={
            "policy_allowed": True,
            "executor_state": "completed",
            "found_dependency_files": found,
        },
    )


def _check_permissions(
    action: Decision,
    cwd: Path,
    observation: Observation | None,
    started: float,
) -> Observation:
    candidates = [cwd]
    command_path = _candidate_path(observation)
    if command_path is not None:
        resolved = _resolve_safe_path(command_path, cwd)
        if resolved is None:
            return _observation(
                action=action,
                cwd=cwd,
                stderr=f"rejected unsafe path candidate: {command_path}",
                duration_ms=_elapsed_ms(started),
                runtime={
                    "policy_allowed": True,
                    "executor_state": "path_rejected",
                    "path_candidate": str(command_path),
                },
            )
        candidates.append(resolved)

    lines: list[str] = []
    for path in candidates:
        exists = path.exists()
        checks = {
            "exists": exists,
            "readable": os.access(path, os.R_OK) if exists else False,
            "writable": os.access(path, os.W_OK) if exists else False,
            "executable": os.access(path, os.X_OK) if exists else False,
        }
        checks_text = ", ".join(f"{key}={value}" for key, value in checks.items())
        lines.append(f"{path}: {checks_text}")

    return _observation(
        action=action,
        cwd=cwd,
        stdout="\n".join(lines),
        duration_ms=_elapsed_ms(started),
        runtime={"policy_allowed": True, "executor_state": "completed"},
    )


def _check_logs(
    action: Decision,
    cwd: Path,
    observation: Observation | None,
    started: float,
) -> Observation:
    if observation is None:
        stderr = "no source observation provided for log inspection"
        runtime = {"policy_allowed": True, "executor_state": "missing_observation"}
        return _observation(
            action=action,
            cwd=cwd,
            stderr=stderr,
            duration_ms=_elapsed_ms(started),
            runtime=runtime,
        )

    stdout = "\n".join(
        (
            "bounded source observation logs:",
            f"stdout_tail_chars={len(observation.stdout_tail)}",
            f"stderr_tail_chars={len(observation.stderr_tail)}",
            "stderr_tail:",
            observation.stderr_tail,
        )
    )
    return _observation(
        action=action,
        cwd=cwd,
        stdout=stdout,
        duration_ms=_elapsed_ms(started),
        runtime={"policy_allowed": True, "executor_state": "completed"},
    )


def _observation(
    *,
    action: Decision,
    cwd: Path,
    duration_ms: int,
    exit_code: int | None = None,
    stdout: str = "",
    stderr: str = "",
    runtime: dict[str, object] | None = None,
) -> Observation:
    return Observation(
        command=f"executor:{action.action}",
        cwd=str(cwd),
        exit_code=exit_code,
        stdout_tail=_tail(stdout),
        stderr_tail=_tail(stderr),
        duration_ms=duration_ms,
        source="kernel_executor",
        policy_summary="explicit read-only executor; no shell commands or writes",
        runtime={"action": action.action, **(runtime or {})},
    )


def _candidate_command(observation: Observation | None) -> str | None:
    if observation is None:
        return None

    match = None
    for text in (observation.stderr_tail, observation.stdout_tail):
        match = _COMMAND_NOT_FOUND_RE.search(text)
        if match:
            return match.group("command").strip("'\"")

    try:
        parts = shlex.split(observation.command)
    except ValueError:
        parts = observation.command.split()
    if not parts or parts[0].startswith("agent_tool:"):
        return None
    return Path(parts[0]).name if "/" in parts[0] else parts[0]


def _candidate_path(observation: Observation | None) -> Path | None:
    if observation is None:
        return None
    try:
        parts = shlex.split(observation.command)
    except ValueError:
        parts = observation.command.split()
    for part in parts[1:]:
        if part.startswith("-"):
            continue
        return Path(part)
    return None


def _resolve_safe_path(path: Path, cwd: Path) -> Path | None:
    if _is_sensitive_path(path):
        return None

    candidate = path if path.is_absolute() else cwd / path
    try:
        resolved = candidate.resolve(strict=False)
        root = cwd.resolve(strict=False)
        resolved.relative_to(root)
    except (OSError, ValueError):
        return None

    if _is_sensitive_path(resolved.relative_to(root)):
        return None
    return resolved


def _is_sensitive_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if parts & SENSITIVE_PATH_PARTS:
        return True
    lowered = str(path).lower()
    return any(part in lowered for part in ("/.ssh/", "/.aws/", "private_key"))


def _tail(value: str, limit: int = DEFAULT_TAIL_CHARS) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def _elapsed_ms(started: float) -> int:
    return max(0, int(round((time.monotonic() - started) * 1000)))


_COMMAND_NOT_FOUND_RE = re.compile(
    r"(?:command not found|not found):\s*(?P<command>[A-Za-z0-9_.:/-]+)"
)
