#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "release_ops_status.v0"
MAX_DETAIL_LINES = 8
MAX_DETAIL_CHARS = 240


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    summary: str
    command: list[str] | None = None
    exit_code: int | None = None
    details: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
        }
        if self.command:
            payload["command"] = list(self.command)
        if self.exit_code is not None:
            payload["exit_code"] = self.exit_code
        if self.details:
            payload["details"] = list(self.details)
        return payload


Runner = Callable[[Sequence[str], int], CommandResult]


def collect_status(
    *,
    root: Path = ROOT,
    runner: Runner | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    runner = runner or run_command
    checks = [
        check_command(
            "plan_eng_review",
            ["bash", "scripts/check-plan-eng-review.sh"],
            runner=runner,
            timeout_seconds=timeout_seconds,
        ),
        check_command(
            "ai_team_status",
            ["bash", "scripts/minerva-ai-team-status.sh"],
            runner=runner,
            timeout_seconds=timeout_seconds,
        ),
        check_command(
            "eval_smoke",
            [sys.executable, "-m", "minerva_kernel.eval_smoke"],
            runner=runner,
            timeout_seconds=timeout_seconds,
        ),
        check_cpu_eval(runner=runner, timeout_seconds=timeout_seconds),
        check_command(
            "release_readiness_local",
            [
                sys.executable,
                "scripts/check-release-readiness.py",
                "--skip-external",
                "--install-backend",
                "current",
            ],
            runner=runner,
            timeout_seconds=timeout_seconds,
        ),
        check_task_queue(root),
        check_worktree(runner=runner, timeout_seconds=timeout_seconds),
    ]
    summary = summarize(checks)
    return {
        "schema_version": SCHEMA_VERSION,
        "ready": summary["ready"],
        "status": summary["status"],
        "summary": summary,
        "checks": [check.to_dict() for check in checks],
    }


def run_command(command: Sequence[str], timeout_seconds: int) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def check_command(
    name: str,
    command: list[str],
    *,
    runner: Runner,
    timeout_seconds: int,
) -> CheckResult:
    try:
        completed = runner(command, timeout_seconds)
    except subprocess.TimeoutExpired:
        return CheckResult(
            name=name,
            status="fail",
            summary=f"timed out after {timeout_seconds}s",
            command=command,
        )

    status = "pass" if completed.returncode == 0 else "fail"
    summary = first_meaningful_line(completed.stdout, completed.stderr)
    if not summary:
        summary = "command passed" if status == "pass" else "command failed"
    return CheckResult(
        name=name,
        status=status,
        summary=summary,
        command=command,
        exit_code=completed.returncode,
        details=safe_details(completed.stdout, completed.stderr),
    )


def check_cpu_eval(*, runner: Runner, timeout_seconds: int) -> CheckResult:
    command = [sys.executable, "-m", "minerva_kernel.cpu_model_eval"]
    try:
        completed = runner(command, timeout_seconds)
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="cpu_model_eval_fixture",
            status="fail",
            summary=f"timed out after {timeout_seconds}s",
            command=command,
        )

    if completed.returncode != 0:
        return CheckResult(
            name="cpu_model_eval_fixture",
            status="fail",
            summary=first_meaningful_line(completed.stdout, completed.stderr)
            or "command failed",
            command=command,
            exit_code=completed.returncode,
            details=safe_details(completed.stdout, completed.stderr),
        )

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return CheckResult(
            name="cpu_model_eval_fixture",
            status="fail",
            summary="cpu eval did not return JSON",
            command=command,
            exit_code=completed.returncode,
            details=safe_details(completed.stdout, completed.stderr),
        )

    decision = payload.get("decision")
    case_count = payload.get("corpus", {}).get("case_count")
    if decision != "promote":
        return CheckResult(
            name="cpu_model_eval_fixture",
            status="fail",
            summary=f"cpu eval decision={decision}",
            command=command,
            exit_code=completed.returncode,
            details=safe_details(completed.stdout, completed.stderr),
        )
    return CheckResult(
        name="cpu_model_eval_fixture",
        status="pass",
        summary=f"cpu eval decision=promote cases={case_count}",
        command=command,
        exit_code=completed.returncode,
    )


def check_task_queue(root: Path) -> CheckResult:
    board = root / ".tasks" / "board.md"
    if not board.exists():
        return CheckResult(
            name="task_queue",
            status="fail",
            summary="missing .tasks/board.md",
        )

    done = 0
    pending = 0
    for line in board.read_text(encoding="utf-8").splitlines():
        columns = [part.strip() for part in line.split("|")]
        if len(columns) < 5:
            continue
        status = columns[3]
        if status == "done":
            done += 1
        elif status == "pending":
            pending += 1

    status = "pass" if pending == 0 else "fail"
    return CheckResult(
        name="task_queue",
        status=status,
        summary=f"done={done} pending={pending}",
    )


def check_worktree(*, runner: Runner, timeout_seconds: int) -> CheckResult:
    command = ["git", "status", "--porcelain"]
    try:
        completed = runner(command, timeout_seconds)
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="worktree",
            status="fail",
            summary=f"timed out after {timeout_seconds}s",
            command=command,
        )
    if completed.returncode != 0:
        return CheckResult(
            name="worktree",
            status="fail",
            summary="git status failed",
            command=command,
            exit_code=completed.returncode,
            details=safe_details(completed.stdout, completed.stderr),
        )

    changed = [line for line in completed.stdout.splitlines() if line.strip()]
    if changed:
        return CheckResult(
            name="worktree",
            status="fail",
            summary=f"dirty worktree entries={len(changed)}",
            command=command,
            exit_code=completed.returncode,
            details=safe_details("\n".join(changed[:MAX_DETAIL_LINES]), ""),
        )
    return CheckResult(
        name="worktree",
        status="pass",
        summary="clean worktree",
        command=command,
        exit_code=completed.returncode,
    )


def summarize(checks: Sequence[CheckResult]) -> dict[str, Any]:
    counts = {"pass": 0, "fail": 0, "skip": 0}
    for check in checks:
        counts[check.status] = counts.get(check.status, 0) + 1
    ready = counts.get("fail", 0) == 0
    return {
        "ready": ready,
        "status": "ready" if ready else "not_ready",
        "pass": counts.get("pass", 0),
        "fail": counts.get("fail", 0),
        "skip": counts.get("skip", 0),
    }


def first_meaningful_line(*chunks: str) -> str:
    for chunk in chunks:
        for line in chunk.splitlines():
            text = line.strip()
            if text:
                return text[:MAX_DETAIL_CHARS]
    return ""


def safe_details(*chunks: str) -> list[str]:
    lines: list[str] = []
    for chunk in chunks:
        for line in chunk.splitlines():
            text = line.strip()
            if not text:
                continue
            lines.append(text[:MAX_DETAIL_CHARS])
            if len(lines) >= MAX_DETAIL_LINES:
                return lines
    return lines


def print_human(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    print(f"Release ops status: {summary['status']}")
    print(
        "Checks: "
        f"pass={summary['pass']} fail={summary['fail']} skip={summary['skip']}"
    )
    for check in payload["checks"]:
        print(f"- [{check['status']}] {check['name']}: {check['summary']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize local Minerva release operations readiness.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Always exit 0 after printing the dashboard.",
    )
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)

    payload = collect_status(timeout_seconds=args.timeout)
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print_human(payload)
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))

    if args.no_fail or payload["ready"]:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
