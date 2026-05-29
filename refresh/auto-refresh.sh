#!/bin/bash
# Weekly batch refresh for the NYC Charter Explorer.
# Pulls the Charter from American Legal Publishing, rebuilds, and — only if the
# source actually changed — commits, pushes to joshgreenman1973, and iMessages Josh.
# Scheduled by ~/Library/LaunchAgents/com.joshgreenman.charter-refresh.plist
#
# Notifications go to iMessage 9175823254 (per standing preference), never Slack.

set -uo pipefail
export PATH="/usr/local/bin:/Users/joshgreenman/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

PROJECT="/Users/joshgreenman/Experiments/nyc-charter-explorer"
LOG="$PROJECT/refresh/auto-refresh.log"
PHONE="+19175823254"
cd "$PROJECT" || exit 1

ts() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(ts)] $*" >> "$LOG"; }

notify() {
  # Send an iMessage via Messages.app. Best-effort; failure is logged, not fatal.
  /usr/bin/osascript <<APPLESCRIPT 2>>"$LOG" || log "osascript notify failed"
tell application "Messages"
  send "$1" to buddy "$PHONE" of (service 1 whose service type is iMessage)
end tell
APPLESCRIPT
}

log "=== refresh run start ==="
OUT="$(/usr/bin/python3 refresh.py 2>&1)"
echo "$OUT" >> "$LOG"

if echo "$OUT" | grep -q "^ABORT"; then
  log "ABORT detected — fetch looked broken; not deploying"
  notify "NYC Charter refresh FAILED (source fetch looked broken). Site left unchanged."
  exit 1
fi

if echo "$OUT" | grep -q "^DONE. CHANGED"; then
  NOW="$(echo "$OUT" | grep 'now:' | head -1 | sed 's/.*now: //; s/^.//; s/.$//')"
  log "CHANGED — committing and deploying"
  git add -A
  git commit -m "Auto-refresh Charter from American Legal Publishing ($(date +%Y-%m-%d))" >> "$LOG" 2>&1
  gh auth switch --user joshgreenman1973 >> "$LOG" 2>&1
  if git push origin main >> "$LOG" 2>&1; then
    gh auth switch --user vitalcity-nyc >> "$LOG" 2>&1
    log "pushed OK"
    notify "NYC Charter Explorer auto-updated and deployed. $NOW — https://joshgreenman1973.github.io/nyc-charter-explorer/"
  else
    gh auth switch --user vitalcity-nyc >> "$LOG" 2>&1
    log "push FAILED"
    notify "NYC Charter refresh built locally but the push FAILED. Needs a look."
  fi
else
  # build.py stamps a fresh "generated"/"indexedAt" timestamp every run, so even a
  # no-op rebuild dirties these artifacts. Restore them so the tree stays clean.
  log "UNCHANGED — restoring regenerated artifacts, nothing to deploy"
  git checkout -- charter-data.js charter-data.json data/versions.json \
    NYC-Charter-for-NotebookLM.md NYC-Charter-for-NotebookLM.txt 2>>"$LOG"
fi
log "=== refresh run end ==="
