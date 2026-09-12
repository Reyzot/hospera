#!/bin/bash
# Igual que run_daily_reviewmonitor.sh: se lanza cada 30 min via launchd,
# pero solo ejecuta guest_followup.py una vez al día, a partir de las 9:00.
MARKER=~/hospera/.last_guestfollowup_run
TODAY=$(date +%F)
HOUR=$(date +%H)

if [ "$HOUR" -lt 9 ]; then
  exit 0
fi

if [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "$TODAY" ]; then
  exit 0
fi

cd ~/hospera
/usr/bin/python3 guest_followup.py
echo "$TODAY" > "$MARKER"
