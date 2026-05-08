#!/usr/bin/env bash
set -euo pipefail

# Run one bounded Minerva AI-team task tick.
#
# This script is designed for launchd, systemd user timers, or cron.
# It selects the first pending task from .tasks/board.md and runs one worker.

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

if ! command -v codex >/dev/null 2>&1 && ! command -v claude >/dev/null 2>&1; then
    printf 'Minerva AI team tick skipped: no supported AI executor found.\n'
    exit 0
fi

if [[ -n "$(git status --short)" ]]; then
    printf 'Minerva AI team tick skipped: worktree is not clean.\n'
    git status --short
    exit 0
fi

TASK_ID="$(awk -F'|' '/\| T[0-9]+ \| #[0-9]+ \| pending \|/ {gsub(/^ +| +$/, "", $2); print $2; exit}' .tasks/board.md)"

if [[ -z "$TASK_ID" ]]; then
    printf 'Minerva AI team tick: no pending task.\n'
    exit 0
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE="$LOG_DIR/${STAMP}-${TASK_ID}.log"

printf 'Minerva AI team tick: running %s\n' "$TASK_ID" | tee "$LOG_FILE"

set +e
bash scripts/agent-loop.sh "$TASK_ID" 2>&1 | tee -a "$LOG_FILE"
status="${PIPESTATUS[0]}"
set -e

printf '\nMinerva AI team tick finished with status %s\n' "$status" | tee -a "$LOG_FILE"
exit "$status"
