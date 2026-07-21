#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-utils.sh" 2>/dev/null || true

require_root

head "Web Interface Setup"

VENV_DIR="$INSTALL_DIR/player/.venv"

cat > /etc/systemd/system/hue-api.service << 'SERVICE'
[Unit]
Description=HueMedia API Server (port 5000)
After=network.target local-fs.target
Wants=local-fs.target

[Service]
Type=simple
User=hue
WorkingDirectory=/opt/hue-media/server
ExecStartPre=/bin/bash -c 'while ! mountpoint -q /pool/Music 2>/dev/null && [ ! -f /opt/hue-media/.setup-complete ]; do sleep 2; done'
ExecStart=/opt/hue-media/player/.venv/bin/python /opt/hue-media/server/run.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
Environment=FLASK_ENV=production

[Install]
WantedBy=multi-user.target
SERVICE

if [ -f "$INSTALL_DIR/server/requirements.txt" ]; then
  log "Installing API server dependencies..."
  "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/server/requirements.txt" 2>&1 | tail -3 || warn "pip install failed"
fi

if [ -d "$INSTALL_DIR/web/dist" ]; then
  log "Using pre-built web UI"
else
  if command -v npm &>/dev/null; then
    log "Building web UI from source (this may take a minute)..."
    cd "$INSTALL_DIR/web"
    npm install 2>&1 | tail -5 || warn "npm install failed"
    npm run build 2>&1 | tail -5 && log "Web UI built" || warn "Web UI build failed"
  else
    log "npm not found — web UI pre-built files will be used if available"
  fi
fi

systemctl enable hue-api.service 2>/dev/null || true
PI_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
log "Web interface: http://${PI_IP}:5000"