#!/bin/bash
# Batch refresh for the NYC Charter Explorer.
# Pulls the Charter from American Legal Publishing, rebuilds, and — only if the
# source actually changed — commits and pushes to joshgreenman1973.
#
# This script does the deterministic heavy lifting only. It is invoked by a weekly
# scheduled Claude task (~/.claude/scheduled-tasks/charter-refresh), which reads the
# RESULT line below and, on a real change, adds a Google Calendar reminder to
# re-upload the file to NotebookLM. No iMessage (that channel was unreliable).
#
# It prints exactly one machine-readable RESULT line as its last stdout line:
#   RESULT: CHANGED | <new currency string>
#   RESULT: UNCHANGED
#   RESULT: ABORT | <reason>

set -uo pipefail
export PATH="/usr/local/bin:/Users/joshgreenman/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

PROJECT="/Users/joshgreenman/Experiments/nyc-charter-explorer"
LOG="$PROJECT/refresh/auto-refresh.log"
cd "$PROJECT" || { echo "RESULT: ABORT | cannot cd to project"; exit 1; }

ts() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(ts)] $*" >> "$LOG"; }

log "=== refresh run start ==="
OUT="$(/usr/bin/python3 refresh.py 2>&1)"
echo "$OUT" >> "$LOG"

if echo "$OUT" | grep -q "^ABORT"; then
  log "ABORT — fetch looked broken; not deploying"
  echo "RESULT: ABORT | source fetch looked broken; site left unchanged"
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
    echo "RESULT: CHANGED | $NOW"
  else
    gh auth switch --user vitalcity-nyc >> "$LOG" 2>&1
    log "push FAILED"
    echo "RESULT: ABORT | built locally but git push failed"
    exit 1
  fi
else
  # build.py stamps a fresh "generated"/"indexedAt" timestamp every run, so even a
  # no-op rebuild dirties these artifacts. Restore them so the tree stays clean.
  log "UNCHANGED — restoring regenerated artifacts, nothing to deploy"
  git checkout -- charter-data.js charter-data.json data/versions.json \
    NYC-Charter-for-NotebookLM.md NYC-Charter-for-NotebookLM.txt 2>>"$LOG"
  echo "RESULT: UNCHANGED"
fi
log "=== refresh run end ==="
