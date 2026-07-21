#!/bin/bash
# HueMedia kiosk session — launched by LightDM on user login

xset s off
xset -dpms

# Wait for the API server to be ready
for i in $(seq 1 30); do
  if curl -s http://localhost:5000/api/status >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

exec chromium-browser \
  --kiosk \
  --no-first-run \
  --disable-features=Translate \
  --disable-sync \
  --no-default-browser-check \
  --disable-notifications \
  --disable-infobars \
  --disk-cache-dir=/dev/null \
  http://localhost:5000
