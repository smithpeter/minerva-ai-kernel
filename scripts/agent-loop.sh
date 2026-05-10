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

EXPECTED_ROOT="${MINERVA_PROJECT_ROOT:-$ROOT}"

if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
    printf 'ERROR: expected Minerva root %s, got %s\n' "$EXPECTED_ROOT" "$ROOT"
    exit 2
fi

TID="${1:?Usage: bash scripts/agent-loop.sh T<number>}"
TASK_FILE=".tasks/${TID}.task.md"
BOARD=".tasks/board.md"

if [[ ! "$TID" =~ ^T[1-9][0-9]*$ ]]; then
    printf 'ERROR: terminal id must be T<number>\n'
    exit 2
fi

if [[ ! -f "$TASK_FILE" ]]; then
    printf 'ERROR: task file not found: %s\n' "$TASK_FILE"
    exit 2
fi

export TERMINAL_ID="$TID"

EXECUTOR="${MINERVA_AI_EXECUTOR:-auto}"

choose_executor() {
    if [[ "$EXECUTOR" == "codex" ]]; then
        command -v codex >/dev/null 2>&1 || return 1
        printf 'codex'
        return 0
    fi
    if [[ "$EXECUTOR" == "claude" ]]; then
        command -v claude >/dev/null 2>&1 || return 1
        printf 'claude'
        return 0
    fi
    if command -v codex >/dev/null 2>&1; then
        printf 'codex'
        return 0
    fi
    if command -v claude >/dev/null 2>&1; then
        printf 'claude'
        return 0
    fi
    return 1
}

run_worker() {
    local prompt="$1"
    local selected
    if ! selected="$(choose_executor)"; then
        printf 'ERROR: no supported AI executor found. Install/auth Codex or Claude Code.\n'
        return 127
    fi

    printf '[%s] executor: %s\n' "$TID" "$selected"

    if [[ "$selected" == "codex" ]]; then
        codex exec --ephemeral --sandbox workspace-write --cd "$ROOT" "$prompt"
        return $?
    fi

    claude --allowedTools "Read,Write,Edit,Glob,Grep,Bash" -p "$prompt"
}

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

    run_worker "You are a Minerva AI team worker running as ${TID}. Before editing, confirm git root is ${EXPECTED_ROOT}. Do not read or modify /Users/zouyongming/VoxSign or unrelated repositories. Read ${TASK_FILE} and docs/plan-eng-review-workflow.md, then execute only that task. For substantial code, eval, integration, security, release, or workflow changes, write a concise Plan-Eng Review before editing project files: scope challenge, what exists, NOT in scope, ASCII flow/state diagram, failure modes, test/eval plan, and parallelization note. Set Status to in_progress at start. Respect Allowed Files and Non-Goals. Run the listed Test / Eval command before completion. Set Status to done only when acceptance criteria are met and no critical Plan-Eng failure-mode gap remains. Write concrete results in the Output section."

    printf '\n[%s] Worker exited. Rechecking task status...\n' "$TID"
    sleep 2
done

printf '[%s] Agent loop finished. Runs: %s\n' "$TID" "$run_count"
