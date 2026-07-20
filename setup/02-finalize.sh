#!/bin/bash
# Final system setup — runs AFTER LCD driver is confirmed working
# Triggered by recovery server on successful boot

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-utils.sh" 2>/dev/null || true

require_root

head "HueMedia Final Setup"

# Mark that we're in setup phase
touch /tmp/hue-media-setup

# ---------------------------------------------------------------
# Step 1: System Dependencies
# ---------------------------------------------------------------
head "Installing System Dependencies"

if has_cmd apt; then
  apt-get update -qq
  
  apt_install \
    python3 python3-pip python3-venv \
    python3-sdl2 libsdl2-dev libsdl2-ttf-dev libsdl2-image-dev \
    libsdl2-mixer-dev cmake build-essential \
    mpv libmpv-dev \
    bluez bluez-tools pulseaudio-module-bluetooth \
    samba samba-common-bin \
    mergerfs \
    exfat-fuse exfatprogs ntfs-3g \
    udisks2 \
    git curl wget \
    alsa-utils \
    python3-dbus \
    i2c-tools \
    xinput-calibrator
fi

# ---------------------------------------------------------------
# Step 2: Python Virtual Environment
# ---------------------------------------------------------------
head "Python Environment"

PLAYER_DIR="$INSTALL_DIR/player"
VENV_DIR="$PLAYER_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$PLAYER_DIR/requirements.txt" -q

# Install pysdl2 with SDL2 image/ttf support
if has_cmd apt; then
  apt_install python3-pysdl2 2>/dev/null || true
fi

SERVER_DIR="$INSTALL_DIR/server"
if [ -d "$SERVER_DIR" ]; then
  "$VENV_DIR/bin/pip" install -r "$SERVER_DIR/requirements.txt" -q
fi

chown -R "$HUE_USER:$HUE_USER" "$INSTALL_DIR"

# ---------------------------------------------------------------
# Step 3: Storage Setup
# ---------------------------------------------------------------
head "Storage Setup"

bash "$SCRIPT_DIR/03-storage.sh"

# ---------------------------------------------------------------
# Step 4: Bluetooth Setup
# ---------------------------------------------------------------
head "Bluetooth Setup"

bash "$SCRIPT_DIR/04-bluetooth.sh"

# ---------------------------------------------------------------
# Step 5: MPV & Player Setup
# ---------------------------------------------------------------
head "Player Setup"

bash "$SCRIPT_DIR/05-player.sh"

# ---------------------------------------------------------------
# Step 6: SAMBA Setup
# ---------------------------------------------------------------
head "SAMBA Setup"

bash "$SCRIPT_DIR/06-samba.sh"

# ---------------------------------------------------------------
# Step 7: Web Interface Setup
# ---------------------------------------------------------------
head "Web Interface Setup"

bash "$SCRIPT_DIR/07-web.sh"

# ---------------------------------------------------------------
# Step 8: Enable All Services
# ---------------------------------------------------------------
head "Enabling Services"

systemctl daemon-reload

for svc in hue-player hue-api hue-bluetooth hue-automount; do
  if [ -f "/etc/systemd/system/$svc.service" ]; then
    systemctl enable "$svc.service" 2>/dev/null || true
    systemctl restart "$svc.service" 2>/dev/null || true
  fi
done

# ---------------------------------------------------------------
# Step 9: Cleanup Recovery Server
# ---------------------------------------------------------------
head "Finalizing"

# Remove the phase1 marker
rm -f /boot/hue-media-phase1 /boot/firmware/hue-media-phase1

# Recovery server stays installed but disabled — can be re-enabled if needed
systemctl disable hue-recovery.service 2>/dev/null || true
systemctl stop hue-recovery.service 2>/dev/null || true

# Mark setup complete
touch /opt/hue-media/.setup-complete

log "HueMedia setup complete!"
echo ""
echo -e "  ${GREEN}Display Player:${NC}  Starts automatically on the LCD"
echo -e "  ${GREEN}Web Interface:${NC}   http://10.0.0.174:5000"
echo -e "  ${GREEN}SAMBA Share:${NC}     \\\\10.0.0.174\\music"
echo -e "  ${GREEN}SSH Access:${NC}      ssh hue@10.0.0.174"
echo ""

rm -f /tmp/hue-media-setup

# Final reboot
log "Rebooting into HueMedia..."
reboot
