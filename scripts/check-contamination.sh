#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EXPECTED_ROOT="/Users/zouyongming/projects/minerva-ai-kernel"

if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
    printf 'ERROR: expected Minerva root %s, got %s\n' "$EXPECTED_ROOT" "$ROOT"
    exit 2
fi

cd "$ROOT"

fail=0

check_forbidden() {
    local label="$1"
    local pattern="$2"
    shift 2
    local output
    output="$(rg -n "$pattern" "$@" 2>/dev/null || true)"
    if [[ -n "$output" ]]; then
        printf '\nERROR: forbidden %s found:\n%s\n' "$label" "$output"
        fail=1
    fi
}

check_forbidden "VoxSign Python import" '(^|[^A-Za-z0-9_])(from|import)[[:space:]]+voxsign([[:space:].]|$)' minerva_kernel tests evals examples adapters policies taxonomies
check_forbidden "VOXSIGN environment namespace" 'VOXSIGN_' minerva_kernel tests evals examples adapters policies taxonomies .github
check_forbidden "VoxSign state directory" '(\.voxsign|~/\.voxsign|/Users/zouyongming/\.voxsign)' minerva_kernel tests evals examples adapters policies taxonomies .github
check_forbidden "VoxSign forbidden root outside boundary docs" '/Users/zouyongming/VoxSign' minerva_kernel tests evals examples adapters policies taxonomies .github

if [[ "$fail" -ne 0 ]]; then
    printf '\nContamination scan failed.\n'
    exit 2
fi

printf 'OK: no VoxSign contamination found in Minerva runtime paths.\n'

