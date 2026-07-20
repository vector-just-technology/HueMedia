#!/bin/bash
# Install media player dependencies and services

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-utils.sh" 2>/dev/null || true

require_root

head "Media Player Setup"

VENV_DIR="$INSTALL_DIR/player/.venv"

# ---------------------------------------------------------------
# ALSA configuration for LCD-35-Show (audio via GPIO/HDMI)
# ---------------------------------------------------------------
mkdir -p /etc/alsa/conf.d

cat > /etc/asound.conf << 'ASOUND'
defaults.pcm.card 0
defaults.ctl.card 0

pcm.!default {
  type hw
  card 0
}

ctl.!default {
  type hw
  card 0
}
ASOUND

# ---------------------------------------------------------------
# Systemd service for the display player
# ---------------------------------------------------------------
cat > /etc/systemd/system/hue-player.service << 'SERVICE'
[Unit]
Description=HueMedia Touchscreen Player
After=graphical.target local-fs.target bluetooth.target
Wants=local-fs.target

[Service]
Type=simple
User=hue
WorkingDirectory=/opt/hue-media/player
Environment=SDL_FBDEV=/dev/fb1
Environment=SDL_MOUSEDEV=/dev/input/touchscreen
Environment=SDL_MOUSEDRV=evdev
Environment=SDL_VIDEODRIVER=fbcon
Environment=DISPLAY=
ExecStartPre=/usr/bin/sleep 5
ExecStart=/opt/hue-media/player/.venv/bin/python /opt/hue-media/player/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

# ---------------------------------------------------------------
# Install requirements
# ---------------------------------------------------------------
if [ -f "$INSTALL_DIR/player/requirements.txt" ]; then
  "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/player/requirements.txt" -q
fi

systemctl enable hue-player.service

log "Player service installed and enabled"
