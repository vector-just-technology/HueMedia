#!/bin/bash
set -e

REPO="https://github.com/vector-just-technology/HueMedia.git"
INSTALL_DIR="/opt/hue-media"
HUE_USER="hue"
HUE_HOME="/home/${HUE_USER}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[x]${NC} $1"; }
head() { echo -e "\n${CYAN}=== $1 ===${NC}"; }

cleanup() {
  if [ $? -ne 0 ]; then
    err "Installation failed"
  fi
}
trap cleanup EXIT

echo -e "${CYAN}"
echo "  _   _             __  __      _ _       "
echo " | | | | ___  ___  |  \/  | ___ (_) |_ ___ "
echo " | |_| |/ _ \/ _ \ | |\/| |/ _ \| | __/ __|"
echo " |  _  |  __/  __/ | |  | |  __/| | |_\__ \\"
echo " |_| |_|\___|\___| |_|  |_|\___|/ |\__|___/"
echo "                             |__/           "
echo -e "${NC}"
  echo "  Lightweight Media Player for Raspberry Pi 3B"
echo "========================================================="

# Root check
if [ "$(id -u)" -ne 0 ]; then
  echo ""
  err "Must run as root (use sudo)"
  exit 1
fi

head "System Check"
if [ ! -f /proc/device-tree/model ] || ! grep -qi "raspberry pi 3" /proc/device-tree/model 2>/dev/null; then
  warn "Not detected as Raspberry Pi 3 — proceeding anyway"
else
  log "Detected: $(tr -d '\0' < /proc/device-tree/model)"
fi

if ! grep -qi "debian\|raspbian" /etc/os-release 2>/dev/null; then
  warn "Not Debian/Raspbian — some package names may differ"
fi

head "Setting up HueMedia user"
if ! id "$HUE_USER" &>/dev/null; then
  useradd -m -s /bin/bash "$HUE_USER"
  usermod -aG audio,video,input,gpio,i2c,spi "$HUE_USER"
  log "Created user: $HUE_USER"
else
  log "User $HUE_USER exists"
fi

head "Cloning Repository"
if [ -d "$INSTALL_DIR" ]; then
  warn "Directory $INSTALL_DIR exists — updating"
  cd "$INSTALL_DIR"
  git pull --ff-only 2>/dev/null || true
else
  log "Cloning into $INSTALL_DIR"
  git clone "$REPO" "$INSTALL_DIR"
fi
chown -R "$HUE_USER:$HUE_USER" "$INSTALL_DIR"

cd "$INSTALL_DIR"

head "Static IP Configuration"
cat > /etc/systemd/system/hue-static-ip.service << 'SERVICE'
[Unit]
Description=HueMedia static IP configuration
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bash /opt/hue-media/scripts/setup-static-ip.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE

chmod +x /opt/hue-media/scripts/setup-static-ip.sh

systemctl daemon-reload
systemctl enable hue-static-ip.service
systemctl start hue-static-ip.service
log "Static IP configured: 10.0.0.174"

# ---------------------------------------------------------------------------
# Install all system dependencies and services
# ---------------------------------------------------------------------------
head "System Setup"
bash setup/02-finalize.sh
