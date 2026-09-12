#!/bin/bash
# Se lanza cada 30 min via launchd (StartInterval), pero solo ejecuta
# review_monitor.py una vez al día, en cuanto sean las 9:00 o más tarde
# y el Mac esté despierto — así no se pierde el día si a las 9:00 en
# punto el portátil estaba dormido.
MARKER=~/hospera/.last_review_run
TODAY=$(date +%F)
HOUR=$(date +%H)

if [ "$HOUR" -lt 9 ]; then
  exit 0
fi

if [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "$TODAY" ]; then
  exit 0
fi

cd ~/hospera
/usr/bin/python3 review_monitor.py --once
echo "$TODAY" > "$MARKER"
