#!/bin/bash
# Auto-update HueMedia on boot if a new GitHub tag is found

INSTALL_DIR="/opt/hue-media"
VERSION_FILE="$INSTALL_DIR/.version"
LOGFILE="/var/log/hue-auto-update.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"; }

if [ ! -d "$INSTALL_DIR/.git" ]; then
  exit 0
fi

cd "$INSTALL_DIR"
export GIT_TERMINAL_PROMPT=0

LATEST_TAG=$(git ls-remote --tags origin 2>/dev/null | grep -v '{}' | awk '{print $2}' | sed 's|refs/tags/||' | sort -V | tail -1)
CURRENT_TAG=$(cat "$VERSION_FILE" 2>/dev/null || echo "")

if [ -z "$LATEST_TAG" ]; then
  log "No remote tags found — skipping update"
  exit 0
fi

if [ "$LATEST_TAG" = "$CURRENT_TAG" ]; then
  log "Already at latest version: $CURRENT_TAG"
  exit 0
fi

log "Updating from $CURRENT_TAG to $LATEST_TAG"
git pull --ff-only origin main 2>&1 | tee -a "$LOGFILE"

log "Re-installing Python dependencies"
VENV_DIR="$INSTALL_DIR/player/.venv"
if [ -d "$VENV_DIR" ]; then
  "$VENV_DIR/bin/pip" install -q --upgrade pip 2>/dev/null || true
  "$VENV_DIR/bin/pip" install -q -r "$INSTALL_DIR/player/requirements.txt" 2>/dev/null || true
  if [ -f "$INSTALL_DIR/server/requirements.txt" ]; then
    "$VENV_DIR/bin/pip" install -q -r "$INSTALL_DIR/server/requirements.txt" 2>/dev/null || true
  fi
fi

log "Reloading systemd and re-enabling services"
systemctl daemon-reload 2>/dev/null || true
for svc in hue-auto-update hue-player hue-api hue-bluetooth hue-automount; do
  systemctl enable "$svc.service" 2>/dev/null || true
done

echo "$LATEST_TAG" > "$VERSION_FILE"
log "Update complete — now on $LATEST_TAG"
