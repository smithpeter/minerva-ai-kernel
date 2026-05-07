#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

section() {
    printf '\n## %s\n\n' "$1"
}

section "Repository"
printf 'root: %s\n' "$ROOT"
if [[ "$ROOT" != "/Users/zouyongming/projects/minerva-ai-kernel" ]]; then
    printf 'ERROR: expected Minerva root, got %s\n' "$ROOT"
    exit 2
fi
printf 'branch: '
git branch --show-current || true
printf 'head: '
git rev-parse --short HEAD || true
printf '\n'
git status --short

section "Boundary"
printf 'project: Minerva\n'
printf 'forbidden roots:\n'
printf -- '- /Users/zouyongming/VoxSign\n'
printf -- '- /Users/zouyongming/VoxSign-decide-review\n'

section "Local Task Board"
if [[ -f .tasks/board.md ]]; then
    sed -n '1,80p' .tasks/board.md
else
    printf 'WARN: .tasks/board.md not found.\n'
fi

section "GitHub Issues"
if command -v gh >/dev/null 2>&1; then
    gh issue list --limit 20 || printf 'WARN: gh issue list failed.\n'
else
    printf 'WARN: gh CLI not found. Use GitHub web or Codex GitHub connector.\n'
fi

section "Recommended Next Action"
printf '1. Assign T1 or T2 to an AI worker.\n'
printf '2. Worker must edit only allowed files in its task card.\n'
printf '3. Worker must run compile/tests and update Output before claiming done.\n'

