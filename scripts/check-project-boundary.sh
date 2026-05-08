#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EXPECTED_ROOT="${MINERVA_PROJECT_ROOT:-/Users/zouyongming/projects/minerva-ai-kernel}"

if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
    printf 'ERROR: expected Minerva root %s, got %s\n' "$EXPECTED_ROOT" "$ROOT"
    exit 2
fi

if [[ "$PWD" == /Users/zouyongming/VoxSign* ]]; then
    printf 'ERROR: current directory is inside forbidden VoxSign root: %s\n' "$PWD"
    exit 2
fi

if [[ "$PWD" == /Users/zouyongming/VoxSign-decide-review* ]]; then
    printf 'ERROR: current directory is inside forbidden VoxSign-decide-review root: %s\n' "$PWD"
    exit 2
fi

if [[ -d /Users/zouyongming/VoxSign/.tasks && -d .tasks ]]; then
    printf 'OK: Minerva has its own .tasks; VoxSign .tasks is separate.\n'
fi

printf 'OK: project boundary verified for %s\n' "$ROOT"
