#!/usr/bin/env bash
set -euo pipefail

# Keep the local AI-team board aligned with task-card status.
#
# This is intentionally mechanical. It does not invent work; it prevents
# completed task cards from being selected again by the automation loop.

ROOT="${MINERVA_PROJECT_ROOT:-/Users/zouyongming/projects/minerva-ai-kernel}"
cd "$ROOT"

bash scripts/check-project-boundary.sh >/dev/null

BOARD=".tasks/board.md"
if [[ ! -f "$BOARD" ]]; then
    printf 'ERROR: missing task board: %s\n' "$BOARD"
    exit 2
fi

tmp="$(mktemp)"
changed=0

while IFS= read -r line; do
    if [[ "$line" =~ ^\|\ (T[0-9]+)\ \|\ (#[0-9]+)\ \|\ ([^|]+)\ \|(.+)$ ]]; then
        task_id="${BASH_REMATCH[1]}"
        github="${BASH_REMATCH[2]}"
        board_status="$(printf '%s' "${BASH_REMATCH[3]}" | xargs)"
        rest="${BASH_REMATCH[4]}"
        task_file=".tasks/${task_id}.task.md"
        if [[ -f "$task_file" ]]; then
            card_status="$(grep "^- Status:" "$task_file" | head -1 | sed 's/- Status: //' | xargs)"
            if [[ -n "$card_status" && "$card_status" != "$board_status" ]]; then
                printf '| %s | %s | %s |%s\n' "$task_id" "$github" "$card_status" "$rest" >>"$tmp"
                changed=1
                continue
            fi
        fi
    fi
    printf '%s\n' "$line" >>"$tmp"
done <"$BOARD"

if [[ "$changed" -eq 1 ]]; then
    mv "$tmp" "$BOARD"
    printf 'Minerva AI team coordinator: board synchronized from task cards.\n'
else
    rm -f "$tmp"
    printf 'Minerva AI team coordinator: board already synchronized.\n'
fi

pending_count="$(awk -F'|' '/\| T[0-9]+ \| #[0-9]+ \| pending \|/ {count++} END {print count + 0}' "$BOARD")"
printf 'Minerva AI team coordinator: pending tasks=%s\n' "$pending_count"
