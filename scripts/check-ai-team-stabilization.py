#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "minerva.ai_team_stabilization.v0"
REQUIRED_FILES = (
    "docs/plan-eng-review-workflow.md",
    "docs/ai-team-task-template.md",
    "docs/ai-team-stabilization.md",
    "scripts/check-plan-eng-review.sh",
    "scripts/release-ops-dashboard.py",
    "scripts/release-handoff.py",
)


def stabilization_status(root: str | Path) -> dict[str, Any]:
    project_root = Path(root)
    board_path = project_root / ".tasks" / "board.md"
    pending = _pending_tasks(board_path)
    missing_files = [
        path for path in REQUIRED_FILES if not (project_root / path).exists()
    ]
    ready = not pending and not missing_files
    return {
        "schema_version": SCHEMA_VERSION,
        "ready": ready,
        "pending_tasks": pending,
        "pending_count": len(pending),
        "missing_required_files": missing_files,
        "next_phase": "release_handoff" if ready else "finish_pending_tasks",
    }


def _pending_tasks(board_path: Path) -> list[str]:
    if not board_path.exists():
        return ["missing-board"]
    pending: list[str] = []
    for line in board_path.read_text(encoding="utf-8").splitlines():
        columns = [part.strip() for part in line.split("|")]
        if len(columns) < 6:
            continue
        task_id = columns[1]
        status = columns[3]
        title = columns[5]
        if task_id.startswith("T") and status == "pending":
            pending.append(f"{task_id}: {title}")
    return pending


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check whether the local AI-team queue can enter stabilization.",
    )
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args(argv)

    payload = stabilization_status(args.root)
    print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if payload["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
