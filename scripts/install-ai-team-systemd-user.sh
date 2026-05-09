#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
SERVICE="$UNIT_DIR/minerva-ai-team-tick.service"
TIMER="$UNIT_DIR/minerva-ai-team-tick.timer"

mkdir -p "$UNIT_DIR" "$ROOT/.minerva/ai-team"

cat > "$SERVICE" <<SERVICE
[Unit]
Description=Minerva AI team bounded task tick
ConditionPathExists=${ROOT}/.tasks/board.md

[Service]
Type=oneshot
WorkingDirectory=${ROOT}
Environment=MINERVA_PROJECT_ROOT=${ROOT}
Environment=MINERVA_AI_EXECUTOR=codex
Environment=PATH=${HOME}/bin:${HOME}/.local/bin:${HOME}/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
ExecStart=/usr/bin/env bash ${ROOT}/scripts/ai-team-tick.sh
SERVICE

cat > "$TIMER" <<TIMER
[Unit]
Description=Run Minerva AI team tick every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
Persistent=true
Unit=minerva-ai-team-tick.service

[Install]
WantedBy=timers.target
TIMER

systemctl --user daemon-reload
systemctl --user enable --now minerva-ai-team-tick.timer

printf 'Installed Minerva AI team systemd user timer: %s\n' "$TIMER"
printf 'Check status with: systemctl --user status minerva-ai-team-tick.timer\n'
printf 'Check logs with: journalctl --user -u minerva-ai-team-tick.service -n 100\n'
