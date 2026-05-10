#!/usr/bin/env bash
set -euo pipefail

ROOT="${MINERVA_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
export MINERVA_PROJECT_ROOT="$ROOT"
cd "$ROOT"

bash scripts/check-project-boundary.sh >/dev/null

pending_count="$(awk -F'|' '/\| T[0-9]+ \| #[0-9]+ \| pending \|/ {count++} END {print count + 0}' .tasks/board.md 2>/dev/null || printf '0')"
dirty_count="$(git status --short | wc -l | tr -d ' ')"

printf 'schema_version=ai_team_preflight.v0\n'
printf 'root=%s\n' "$ROOT"
printf 'branch=%s\n' "$(git branch --show-current 2>/dev/null || true)"
printf 'head=%s\n' "$(git rev-parse --short HEAD 2>/dev/null || true)"
printf 'dirty_count=%s\n' "$dirty_count"
printf 'pending_count=%s\n' "$pending_count"
printf 'codex_available=%s\n' "$(command -v codex >/dev/null 2>&1 && printf true || printf false)"
printf 'claude_available=%s\n' "$(command -v claude >/dev/null 2>&1 && printf true || printf false)"
printf 'plan_eng_review_workflow=%s\n' "$([[ -f docs/plan-eng-review-workflow.md ]] && printf present || printf missing)"

if command -v systemctl >/dev/null 2>&1; then
    if systemctl --user is-active --quiet minerva-ai-team-tick.timer 2>/dev/null; then
        printf 'systemd_timer=active\n'
    else
        printf 'systemd_timer=inactive\n'
    fi
else
    printf 'systemd_timer=unavailable\n'
fi

if [[ "$dirty_count" != "0" ]]; then
    printf 'ready=false\n'
    printf 'reason=worktree_dirty\n'
elif [[ ! -f docs/plan-eng-review-workflow.md ]]; then
    printf 'ready=false\n'
    printf 'reason=missing_plan_eng_review_workflow\n'
elif [[ "$pending_count" == "0" ]]; then
    printf 'ready=false\n'
    printf 'reason=no_pending_tasks\n'
elif ! command -v codex >/dev/null 2>&1 && ! command -v claude >/dev/null 2>&1; then
    printf 'ready=false\n'
    printf 'reason=no_ai_executor\n'
else
    printf 'ready=true\n'
    printf 'reason=ready_for_tick\n'
fi
