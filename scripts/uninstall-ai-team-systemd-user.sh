#!/usr/bin/env bash
set -euo pipefail

UNIT_DIR="$HOME/.config/systemd/user"
SERVICE="$UNIT_DIR/minerva-ai-team-tick.service"
TIMER="$UNIT_DIR/minerva-ai-team-tick.timer"

systemctl --user disable --now minerva-ai-team-tick.timer >/dev/null 2>&1 || true
rm -f "$SERVICE" "$TIMER"
systemctl --user daemon-reload

printf 'Uninstalled Minerva AI team systemd user timer.\n'
