#!/usr/bin/env bash
set -euo pipefail

PLIST="$HOME/Library/LaunchAgents/com.minerva.ai-team.tick.plist"
DOMAIN="gui/$(id -u)"
LABEL="com.minerva.ai-team.tick"

if [[ -f "$PLIST" ]]; then
    launchctl bootout "$DOMAIN/$LABEL" >/dev/null 2>&1 || true
    rm -f "$PLIST"
    printf 'Uninstalled Minerva AI team launchd job.\n'
else
    printf 'Minerva AI team launchd job is not installed.\n'
fi
