#!/usr/bin/env bash
set -euo pipefail

# Local AI-team execution loop for Minerva.
#
# Usage:
#   bash scripts/agent-loop.sh T1
#
# This script is intentionally scoped to /Users/zouyongming/projects/minerva-ai-kernel.
# It must not be run from VoxSign or any other repository.

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

if [[ "$ROOT" != "/Users/zouyongming/projects/minerva-ai-kernel" ]]; then
    printf 'ERROR: expected Minerva root, got %s\n' "$ROOT"
    exit 2
fi

TID="${1:?Usage: bash scripts/agent-loop.sh T1|T2|T3|T4}"
TASK_FILE=".tasks/${TID}.task.md"
BOARD=".tasks/board.md"

if [[ ! "$TID" =~ ^T[1-9]$ ]]; then
    printf 'ERROR: terminal id must be T1-T9\n'
    exit 2
fi

if [[ ! -f "$TASK_FILE" ]]; then
    printf 'ERROR: task file not found: %s\n' "$TASK_FILE"
    exit 2
fi

if ! command -v claude >/dev/null 2>&1; then
    printf 'ERROR: claude CLI not found. Install/auth Claude Code or assign task manually.\n'
    exit 127
fi

export TERMINAL_ID="$TID"

run_count=0
while true; do
    status="$(grep "^- Status:" "$TASK_FILE" | head -1 | sed 's/- Status: //')"

    if [[ "$status" == "done" ]]; then
        printf '[%s] Current task done. Checking board for next pending task...\n' "$TID"
        next_id="$(grep "|.*| pending |" "$BOARD" 2>/dev/null | head -1 | awk -F'|' '{gsub(/^ +| +$/, "", $2); print $2}')"
        if [[ -z "$next_id" ]]; then
            printf '[%s] No pending task found. Exiting.\n' "$TID"
            break
        fi
        printf '[%s] Next pending task is %s. Coordinator should assign it explicitly.\n' "$TID" "$next_id"
        break
    fi

    task_title="$(head -1 "$TASK_FILE" | sed 's/# Task: //')"
    run_count=$((run_count + 1))
    printf '\n[%s] Run #%s: %s\n\n' "$TID" "$run_count" "$task_title"

    claude --allowedTools "Read,Write,Edit,Glob,Grep,Bash" -p "You are a Minerva AI team worker running as ${TID}.
Before editing, confirm git root is /Users/zouyongming/projects/minerva-ai-kernel.
Do not read or modify /Users/zouyongming/VoxSign or unrelated repositories.
Read ${TASK_FILE} and execute only that task.
Set Status to in_progress at start.
Respect Allowed Files and Non-Goals.
Run the listed Test / Eval command before completion.
Set Status to done only when acceptance criteria are met.
Write concrete results in the Output section."

    printf '\n[%s] Worker exited. Rechecking task status...\n' "$TID"
    sleep 2
done

printf '[%s] Agent loop finished. Runs: %s\n' "$TID" "$run_count"

