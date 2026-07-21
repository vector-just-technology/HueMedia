#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-utils.sh" 2>/dev/null || true

require_root

head "Kiosk & Player Setup"

VENV_DIR="$INSTALL_DIR/player/.venv"

# ---------------------------------------------------------------
# ALSA configuration
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
# Kiosk session script
# ---------------------------------------------------------------
chmod +x "$INSTALL_DIR/scripts/kiosk-session.sh"

# LightDM auto-login for hue user
mkdir -p /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/01-hue-kiosk.conf << 'LIGHTDM'
[Seat:*]
autologin-user=hue
autologin-user-timeout=0
LIGHTDM

# Kiosk autostart .desktop entry (system-wide)
mkdir -p /etc/xdg/autostart
cat > /etc/xdg/autostart/hue-kiosk.desktop << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=HueMedia Kiosk
Exec=/opt/hue-media/scripts/kiosk-session.sh
Terminal=false
X-GNOME-Autostart-enabled=true
DESKTOP

# ---------------------------------------------------------------
# Install player Python deps
# ---------------------------------------------------------------
if [ -f "$INSTALL_DIR/player/requirements.txt" ]; then
  log "Installing player dependencies..."
  "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/player/requirements.txt" 2>&1 | tail -3 || warn "pip install failed"
fi

# ---------------------------------------------------------------
# Boot-time auto-update service
# ---------------------------------------------------------------
cat > /etc/systemd/system/hue-auto-update.service << 'SERVICE'
[Unit]
Description=HueMedia Auto-Update (boot-time)
After=network-online.target
Wants=network-online.target
Before=hue-api.service hue-bluetooth.service

[Service]
Type=oneshot
ExecStart=/opt/hue-media/scripts/auto-update.sh
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

chmod +x "$INSTALL_DIR/scripts/auto-update.sh" 2>/dev/null || true
systemctl enable hue-auto-update.service 2>/dev/null || true

log "Player setup complete"