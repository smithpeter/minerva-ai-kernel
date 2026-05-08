#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

section() {
    printf '\n## %s\n\n' "$1"
}

section "Repository"
printf 'root: %s\n' "$ROOT"
bash scripts/check-project-boundary.sh
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
bash scripts/check-contamination.sh

section "Local Task Board"
bash scripts/ai-team-coordinator.sh
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
printf '1. Keep .tasks/board.md populated with small pending tasks.\n'
printf '2. Let launchd/systemd run scripts/ai-team-tick.sh, or kickstart one tick manually.\n'
printf '3. Worker must run compile/tests and update Output before claiming done.\n'
