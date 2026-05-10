#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "minerva.release_handoff.v0"
MAX_PATHS_PER_CATEGORY = 20


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[Sequence[str], int], CommandResult]


def build_handoff(
    *,
    root: Path = ROOT,
    runner: Runner | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    runner = runner or run_command
    dashboard = _load_release_ops_dashboard().collect_status(
        root=root,
        runner=runner,
        timeout_seconds=timeout_seconds,
    )
    git_status = collect_git_status(runner=runner, timeout_seconds=timeout_seconds)
    changed_files = parse_porcelain(git_status.stdout) if git_status.returncode == 0 else []
    inventory = inventory_from_changes(changed_files)
    blockers = blockers_from(dashboard, git_status, inventory)
    return {
        "schema_version": SCHEMA_VERSION,
        "ready_for_release_review": not blockers,
        "dashboard": {
            "schema_version": dashboard["schema_version"],
            "status": dashboard["status"],
            "ready": dashboard["ready"],
            "summary": dashboard["summary"],
        },
        "git_status": {
            "exit_code": git_status.returncode,
            "clean": git_status.returncode == 0 and not changed_files,
            "changed_file_count": len(changed_files),
        },
        "changed_file_inventory": inventory,
        "blockers": blockers,
        "next_actions": next_actions(blockers),
    }


def run_command(command: Sequence[str], timeout_seconds: int) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def collect_git_status(*, runner: Runner, timeout_seconds: int) -> CommandResult:
    try:
        return runner(["git", "status", "--porcelain"], timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        return CommandResult(124, "", f"git status timed out after {exc.timeout}s")


def parse_porcelain(output: str) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for raw_line in output.splitlines():
        if not raw_line.strip():
            continue
        status = raw_line[:2].strip() or "?"
        path = raw_line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changes.append(
            {
                "status": status,
                "path": path,
                "category": categorize_path(path),
            }
        )
    return changes


def inventory_from_changes(changes: Sequence[dict[str, str]]) -> dict[str, Any]:
    categories: dict[str, dict[str, Any]] = {}
    for change in changes:
        category = change["category"]
        bucket = categories.setdefault(category, {"count": 0, "paths": []})
        bucket["count"] += 1
        if len(bucket["paths"]) < MAX_PATHS_PER_CATEGORY:
            bucket["paths"].append(change["path"])
    return {
        "total": len(changes),
        "categories": categories,
    }


def categorize_path(path: str) -> str:
    if path.startswith(".tasks/"):
        return "task_queue"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("docs/") or path == "README.md":
        return "docs"
    if path.startswith("scripts/"):
        return "scripts"
    if path.startswith("minerva_kernel/"):
        return "kernel"
    if path.startswith("evals/"):
        return "evals"
    if path.startswith("examples/"):
        return "examples"
    if path.startswith("taxonomies/") or path.startswith("policies/"):
        return "taxonomy_policy"
    if path.startswith("models/"):
        return "models"
    return "other"


def blockers_from(
    dashboard: dict[str, Any],
    git_status: CommandResult,
    inventory: dict[str, Any],
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    if not dashboard.get("ready"):
        for check in dashboard.get("checks", []):
            if check.get("status") == "fail":
                blockers.append(
                    {
                        "source": "release_ops_dashboard",
                        "name": str(check.get("name", "unknown")),
                        "detail": str(check.get("summary", "failed")),
                    }
                )
    if git_status.returncode != 0:
        blockers.append(
            {
                "source": "git_status",
                "name": "git_status_failed",
                "detail": first_line(git_status.stderr) or "git status failed",
            }
        )
    elif inventory["total"]:
        blockers.append(
            {
                "source": "git_status",
                "name": "dirty_worktree",
                "detail": f"changed_file_count={inventory['total']}",
            }
        )
    return dedupe_blockers(blockers)


def dedupe_blockers(blockers: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for blocker in blockers:
        key = (blocker["source"], blocker["name"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(blocker)
    return deduped


def next_actions(blockers: Sequence[dict[str, str]]) -> list[str]:
    if not blockers:
        return ["record release review decision"]
    actions: list[str] = []
    if any(blocker["name"] == "dirty_worktree" for blocker in blockers):
        actions.append("review, commit, or intentionally defer changed files")
    if any(blocker["source"] == "release_ops_dashboard" for blocker in blockers):
        actions.append("rerun release ops dashboard after addressing failed checks")
    if any(blocker["source"] == "git_status" for blocker in blockers):
        actions.append("rerun git status and release handoff")
    return actions


def first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:240]
    return ""


def _load_release_ops_dashboard():
    path = ROOT / "scripts" / "release-ops-dashboard.py"
    spec = importlib.util.spec_from_file_location("release_ops_dashboard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load release ops dashboard")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def print_human(payload: dict[str, Any]) -> None:
    print("Release handoff: " + ("ready" if payload["ready_for_release_review"] else "blocked"))
    print(f"Dashboard: {payload['dashboard']['status']}")
    print(
        "Worktree: "
        f"clean={payload['git_status']['clean']} "
        f"changed={payload['git_status']['changed_file_count']}"
    )
    for blocker in payload["blockers"]:
        print(f"- blocker {blocker['source']}/{blocker['name']}: {blocker['detail']}")
    for action in payload["next_actions"]:
        print(f"- next: {action}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a local release handoff inventory artifact.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    parser.add_argument("--no-fail", action="store_true", help="Always exit 0.")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)

    payload = build_handoff(timeout_seconds=args.timeout)
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print_human(payload)
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    if args.no_fail or payload["ready_for_release_review"]:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
