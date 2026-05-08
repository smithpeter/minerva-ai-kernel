#!/usr/bin/env bash
set -euo pipefail

# Run a bounded Minerva AI-team task chain.
#
# This script is designed for launchd, systemd user timers, or cron.
# It selects pending tasks from .tasks/board.md and runs workers until the queue
# is empty or a safety limit is reached.

ROOT="${MINERVA_PROJECT_ROOT:-/Users/zouyongming/projects/minerva-ai-kernel}"
cd "$ROOT"

bash scripts/check-project-boundary.sh
bash scripts/check-contamination.sh
bash scripts/ai-team-coordinator.sh

LOG_DIR=".minerva/ai-team/logs"
LOCK_DIR=".minerva/ai-team/lock"
mkdir -p "$LOG_DIR" "$(dirname "$LOCK_DIR")"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    printf 'Minerva AI team tick skipped: another tick is running.\n'
    exit 0
fi
trap 'rmdir "$LOCK_DIR"' EXIT

MAX_TASKS_PER_TICK="${MINERVA_AI_MAX_TASKS_PER_TICK:-4}"
if [[ ! "$MAX_TASKS_PER_TICK" =~ ^[1-9][0-9]*$ ]]; then
    printf 'ERROR: MINERVA_AI_MAX_TASKS_PER_TICK must be a positive integer.\n'
    exit 2
fi

run_count=0
while [[ "$run_count" -lt "$MAX_TASKS_PER_TICK" ]]; do
    bash scripts/ai-team-autopilot.sh

    if ! command -v codex >/dev/null 2>&1 && ! command -v claude >/dev/null 2>&1; then
        printf 'Minerva AI team tick skipped: no supported AI executor found.\n'
        exit 0
    fi

    if [[ -n "$(git status --short)" ]]; then
        printf 'Minerva AI team tick paused: worktree is not clean.\n'
        git status --short
        exit 0
    fi

    TASK_ID="$(awk -F'|' '/\| T[0-9]+ \| #[0-9]+ \| pending \|/ {gsub(/^ +| +$/, "", $2); print $2; exit}' .tasks/board.md)"

    if [[ -z "$TASK_ID" ]]; then
        printf 'Minerva AI team tick: no pending task.\n'
        exit 0
    fi

    run_count=$((run_count + 1))
    STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
    LOG_FILE="$LOG_DIR/${STAMP}-${TASK_ID}.log"

    printf 'Minerva AI team tick: running %s (%s/%s)\n' "$TASK_ID" "$run_count" "$MAX_TASKS_PER_TICK" | tee "$LOG_FILE"

    set +e
    bash scripts/agent-loop.sh "$TASK_ID" 2>&1 | tee -a "$LOG_FILE"
    status="${PIPESTATUS[0]}"
    set -e

    bash scripts/ai-team-autopilot.sh 2>&1 | tee -a "$LOG_FILE"

    if [[ "$status" -ne 0 ]]; then
        printf '\nMinerva AI team tick stopped after %s with status %s\n' "$TASK_ID" "$status" | tee -a "$LOG_FILE"
        exit "$status"
    fi
done

printf 'Minerva AI team tick reached safety limit: %s tasks.\n' "$MAX_TASKS_PER_TICK"
