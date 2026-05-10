#!/usr/bin/env bash
set -euo pipefail

ROOT="${MINERVA_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
export MINERVA_PROJECT_ROOT="$ROOT"
cd "$ROOT"

bash scripts/check-project-boundary.sh >/dev/null

failures=0

require_file() {
    local path="$1"
    if [[ ! -f "$path" ]]; then
        printf 'FAIL missing file: %s\n' "$path"
        failures=$((failures + 1))
    else
        printf 'PASS file: %s\n' "$path"
    fi
}

require_text() {
    local path="$1"
    local pattern="$2"
    local label="$3"
    if [[ ! -f "$path" ]]; then
        printf 'FAIL %s: missing %s\n' "$label" "$path"
        failures=$((failures + 1))
        return
    fi
    if grep -Fq "$pattern" "$path"; then
        printf 'PASS %s\n' "$label"
    else
        printf 'FAIL %s: expected %s in %s\n' "$label" "$pattern" "$path"
        failures=$((failures + 1))
    fi
}

printf 'schema_version=plan_eng_review_check.v0\n'

require_file "docs/plan-eng-review-workflow.md"
require_file "docs/ai-team-task-template.md"

require_text "docs/plan-eng-review-workflow.md" "## Required Plan-Eng Review Block" "workflow required block"
require_text "docs/plan-eng-review-workflow.md" "## Failure-Mode Gate" "workflow failure-mode gate"
require_text "docs/plan-eng-review-workflow.md" "## ASCII Diagram Rules" "workflow ASCII rules"
require_text "docs/ai-team-task-template.md" "## Plan-Eng Review" "task template review block"
require_text "docs/ai-team-task-template.md" "No critical Plan-Eng failure-mode gap remains open." "task template completion gate"
require_text "scripts/agent-loop.sh" "docs/plan-eng-review-workflow.md" "worker reads workflow"
require_text "scripts/agent-loop.sh" "no critical Plan-Eng failure-mode gap remains" "worker completion gate"
require_text "scripts/ai-team-preflight.sh" "plan_eng_review_workflow=" "preflight reports workflow"
require_text "scripts/minerva-ai-team-status.sh" "Plan-Eng Review" "status mentions workflow"
require_text "README.md" "docs/plan-eng-review-workflow.md" "README workflow link"

if [[ "$failures" -ne 0 ]]; then
    printf 'ready=false\n'
    printf 'failures=%s\n' "$failures"
    exit 1
fi

printf 'ready=true\n'
printf 'failures=0\n'
