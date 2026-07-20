#!/bin/bash
# Install the recovery web server (port 3000)
# This runs BEFORE the LCD driver is installed

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-utils.sh" 2>/dev/null || true

require_root

head "Installing Recovery Web Server"

# Install minimal Python deps for the recovery server
if has_cmd apt; then
  apt_install python3 python3-pip python3-flask
fi

pip_install flask

# Create recovery service
cat > /etc/systemd/system/hue-recovery.service << 'SERVICE'
[Unit]
Description=HueMedia Recovery Server (port 3000)
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hue-media/recovery
ExecStart=/usr/bin/python3 /opt/hue-media/recovery/server.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Enable recovery service
systemctl daemon-reload
systemctl enable hue-recovery.service
systemctl restart hue-recovery.service

log "Recovery server installed on port 3000"
log "Access at http://10.0.0.174:3000 if something goes wrong"
