#!/bin/bash
# launchd lo lanza cada 30 min. Solo corre de 9:00 a 20:59 (hora del Mac).
# No duplica mensajes: guest_state/<cliente>.json guarda qué se ha mandado ya.
HOUR=$(date +%H)
if [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 21 ]; then
  exit 0
fi
cd ~/hospera
/usr/bin/python3 guest_followup.py
