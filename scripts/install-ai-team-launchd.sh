#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/zouyongming/projects/minerva-ai-kernel"
PLIST="$HOME/Library/LaunchAgents/com.minerva.ai-team.tick.plist"

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.minerva.ai-team.tick</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${ROOT}/scripts/ai-team-tick.sh</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${ROOT}</string>
  <key>StartInterval</key>
  <integer>1800</integer>
  <key>RunAtLoad</key>
  <false/>
  <key>StandardOutPath</key>
  <string>${ROOT}/.minerva/ai-team/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>${ROOT}/.minerva/ai-team/launchd.err.log</string>
</dict>
</plist>
PLIST

mkdir -p "$ROOT/.minerva/ai-team"
launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"

printf 'Installed Minerva AI team launchd job: %s\n' "$PLIST"
printf 'It runs every 1800 seconds and logs under %s/.minerva/ai-team/.\n' "$ROOT"

