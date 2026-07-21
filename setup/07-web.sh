#!/bin/bash
# Web interface setup (React build + API server)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-utils.sh" 2>/dev/null || true

require_root

head "Web Interface Setup"

VENV_DIR="$INSTALL_DIR/player/.venv"

# ---------------------------------------------------------------
# Flask API server service
# ---------------------------------------------------------------
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

# ---------------------------------------------------------------
# Install server dependencies
# ---------------------------------------------------------------
if [ -f "$INSTALL_DIR/server/requirements.txt" ]; then
  "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/server/requirements.txt" -q
fi

# ---------------------------------------------------------------
# Web UI — use pre-built or build from source
# ---------------------------------------------------------------
if [ -d "$INSTALL_DIR/web/dist" ]; then
  log "Using pre-built web UI"
else
  if has_cmd node && has_cmd npm; then
    log "Building web UI from source"
    cd "$INSTALL_DIR/web"
    npm install --silent 2>/dev/null
    npm run build 2>/dev/null && log "Web UI built successfully" || warn "Web UI build failed — using fallback"
  else
    warn "Node.js not available — web UI will use Flask-served templates"
  fi
fi

# Enable API service
systemctl enable hue-api.service
PI_IP=$(hostname -I | awk '{print $1}')
log "Web interface: http://${PI_IP}:5000"
