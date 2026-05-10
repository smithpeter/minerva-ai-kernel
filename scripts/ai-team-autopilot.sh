#!/usr/bin/env bash
set -euo pipefail

# Finalize completed AI-team work without human handoff.
#
# The script is intentionally conservative:
# - it only acts when changed task cards are already marked done;
# - it refuses to commit in-progress task cards;
# - changed files must stay inside the task's Allowed Files plus task metadata;
# - it runs boundary, contamination, compile, and unit tests before committing.

ROOT="${MINERVA_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
export MINERVA_PROJECT_ROOT="$ROOT"
cd "$ROOT"

bash scripts/check-project-boundary.sh >/dev/null
bash scripts/check-contamination.sh >/dev/null
bash scripts/ai-team-coordinator.sh >/dev/null

if [[ -z "$(git status --short)" ]]; then
    printf 'Minerva AI team autopilot: worktree clean; nothing to finalize.\n'
    exit 0
fi

changed_paths=()
while IFS= read -r path; do
    [[ -n "$path" ]] && changed_paths+=("$path")
done < <(
    {
        git diff --name-only
        git ls-files --others --exclude-standard
    } | sort -u
)

changed_task_files=()
for path in "${changed_paths[@]}"; do
    if [[ "$path" =~ ^\.tasks/T[0-9]+\.task\.md$ ]]; then
        changed_task_files+=("$path")
    fi
done

if [[ "${#changed_task_files[@]}" -eq 0 ]]; then
    printf 'Minerva AI team autopilot: dirty worktree has no changed task card; skipping.\n'
    git status --short
    exit 0
fi

task_id=""
issue_number=""
task_title=""
allowed_prefixes=()

for task_file in "${changed_task_files[@]}"; do
    card_status="$(grep "^- Status:" "$task_file" | head -1 | sed 's/- Status: //' | xargs)"
    if [[ "$card_status" == "in_progress" || "$card_status" == "pending" ]]; then
        printf 'Minerva AI team autopilot: task card is %s; skipping finalize: %s\n' "$card_status" "$task_file"
        exit 0
    fi
    if [[ "$card_status" != "done" ]]; then
        printf 'Minerva AI team autopilot: unknown task card status %s in %s; skipping.\n' "$card_status" "$task_file"
        exit 0
    fi
done

task_file="${changed_task_files[0]}"
task_id="$(basename "$task_file" .task.md)"
task_title="$(head -1 "$task_file" | sed 's/# Task: //')"
issue_number="$(grep "^- GitHub Issue:" "$task_file" | head -1 | sed -E 's#.*/issues/([0-9]+).*#\1#')"

allowed_line="$(grep "^- Allowed Files:" "$task_file" | head -1 || true)"
while IFS= read -r prefix; do
    [[ -n "$prefix" ]] && allowed_prefixes+=("$prefix")
done < <(printf '%s\n' "$allowed_line" | grep -Eo '`[^`]+`' | tr -d '`')

is_allowed_path() {
    local path="$1"
    if [[ "$path" == ".tasks/board.md" || "$path" == "$task_file" ]]; then
        return 0
    fi
    for prefix in "${allowed_prefixes[@]}"; do
        if [[ "$prefix" == */ ]]; then
            [[ "$path" == "$prefix"* ]] && return 0
        else
            [[ "$path" == "$prefix" || "$path" == "$prefix/"* ]] && return 0
        fi
    done
    return 1
}

for path in "${changed_paths[@]}"; do
    if ! is_allowed_path "$path"; then
        printf 'Minerva AI team autopilot: changed path outside task scope; skipping: %s\n' "$path"
        printf 'Allowed prefixes from %s: %s\n' "$task_file" "${allowed_prefixes[*]:-(none)}"
        exit 0
    fi
done

printf 'Minerva AI team autopilot: finalizing %s: %s\n' "$task_id" "$task_title"

bash scripts/check-project-boundary.sh
bash scripts/check-contamination.sh
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
git diff --check

git add "${changed_paths[@]}"

commit_subject="$(printf '%s' "$task_title" | sed 's/`//g')"
git commit -m "$commit_subject"
git push

if [[ -n "$issue_number" && "$issue_number" != "$task_file" ]]; then
    if command -v gh >/dev/null 2>&1; then
        set +e
        gh issue comment "$issue_number" \
            --body "Completed by Minerva AI team autopilot. Commit: $(git rev-parse --short HEAD). Verification: boundary check, contamination check, compileall, and unittest passed."
        gh issue close "$issue_number" --reason completed
        gh_status="$?"
        set -e
        if [[ "$gh_status" -ne 0 ]]; then
            printf 'Minerva AI team autopilot: WARN gh issue update failed for #%s.\n' "$issue_number"
        fi
    else
        printf 'Minerva AI team autopilot: WARN gh not found; issue #%s not updated.\n' "$issue_number"
    fi
fi

printf 'Minerva AI team autopilot: finalized %s at %s.\n' "$task_id" "$(git rev-parse --short HEAD)"
