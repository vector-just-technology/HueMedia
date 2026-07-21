#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-utils.sh" 2>/dev/null || true

require_root
head "HueMedia Final Setup"
touch /tmp/hue-media-setup

head "Installing System Dependencies"
if has_cmd apt; then
  log "Updating package lists (this may take a minute)..."
  apt-get update 2>&1 | tail -3 || warn "apt update failed — continuing anyway"

  log "Installing packages..."
  for pkg in python3 python3-pip python3-venv python3-sdl2 libsdl2-dev \
      libsdl2-ttf-dev libsdl2-image-dev libsdl2-mixer-dev cmake build-essential \
      mpv libmpv-dev bluez bluez-tools pulseaudio-module-bluetooth \
      samba samba-common-bin mergerfs exfat-fuse exfatprogs ntfs-3g \
      udisks2 git curl wget alsa-utils python3-dbus i2c-tools xinput-calibrator; do
    DEBIAN_FRONTEND=noninteractive apt-get install -y "$pkg" 2>&1 | tail -1 || warn "Failed to install $pkg — continuing"
  done
fi

head "Python Environment"
PLAYER_DIR="$INSTALL_DIR/player"
VENV_DIR="$PLAYER_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR" 2>&1 | tail -1 || { err "Failed to create venv"; exit 1; }
fi

"$VENV_DIR/bin/pip" install --upgrade pip -q 2>/dev/null || true

if [ -f "$PLAYER_DIR/requirements.txt" ]; then
  log "Installing player dependencies..."
  "$VENV_DIR/bin/pip" install -r "$PLAYER_DIR/requirements.txt" 2>&1 | tail -3 || warn "pip install failed"
fi

if has_cmd apt; then
  apt-get install -y python3-pysdl2 2>/dev/null || true
fi

SERVER_DIR="$INSTALL_DIR/server"
if [ -f "$SERVER_DIR/requirements.txt" ]; then
  log "Installing server dependencies..."
  "$VENV_DIR/bin/pip" install -r "$SERVER_DIR/requirements.txt" 2>&1 | tail -3 || warn "pip install failed"
fi

chown -R "$HUE_USER:$HUE_USER" "$INSTALL_DIR" 2>/dev/null || true

head "Storage Setup"
bash "$SCRIPT_DIR/03-storage.sh"

head "Bluetooth Setup"
bash "$SCRIPT_DIR/04-bluetooth.sh"

head "Player Setup"
bash "$SCRIPT_DIR/05-player.sh"

head "SAMBA Setup"
bash "$SCRIPT_DIR/06-samba.sh"

head "Web Interface Setup"
bash "$SCRIPT_DIR/07-web.sh"

head "Enabling Services"
systemctl daemon-reload 2>/dev/null || true
for svc in hue-auto-update hue-player hue-api hue-bluetooth hue-automount; do
  if [ -f "/etc/systemd/system/$svc.service" ]; then
    systemctl enable "$svc.service" 2>/dev/null && log "Enabled $svc" || warn "Could not enable $svc"
  fi
done

head "Finalizing"
touch /opt/hue-media/.setup-complete
log "HueMedia setup complete!"
PI_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$PI_IP" ] && PI_IP="<pi-ip>"
echo ""
echo -e "  ${GREEN}Display Player:${NC}  Starts automatically"
echo -e "  ${GREEN}Web Interface:${NC}   http://${PI_IP}:5000"
echo -e "  ${GREEN}SAMBA Share:${NC}     \\\\${PI_IP}\\music"
echo -e "  ${GREEN}SSH Access:${NC}      ssh hue@${PI_IP}"
echo ""
rm -f /tmp/hue-media-setup

log "Installation finished — rebooting..."
reboot || { warn "Reboot failed — please reboot manually"; exit 0; }