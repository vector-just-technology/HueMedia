#!/bin/bash

REPO="https://github.com/vector-just-technology/HueMedia.git"
INSTALL_DIR="/opt/hue-media"
HUE_USER="hue"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[x]${NC} $1"; }
head() { echo -e "\n${CYAN}=== $1 ===${NC}"; }

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

if [ "$(id -u)" -ne 0 ]; then
  echo ""
  err "Must run as root (use sudo)"
  exit 1
fi

head "System Check"
if [ -f /proc/device-tree/model ]; then
  log "Detected: $(tr -d '\0' < /proc/device-tree/model)"
else
  warn "Not a Raspberry Pi — proceeding anyway"
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
export GIT_TERMINAL_PROMPT=0
if [ -d "$INSTALL_DIR" ]; then
  if [ -d "$INSTALL_DIR/.git" ]; then
    log "Updating existing repository"
    cd "$INSTALL_DIR"
    git remote set-url origin "$REPO" 2>/dev/null || true
    git fetch origin 2>&1 | tail -2 || true
    git reset --hard origin/main 2>&1 | tail -1 || true
  else
    warn "Directory exists but not a git repo — re-cloning"
    rm -rf "$INSTALL_DIR"
    git clone "$REPO" "$INSTALL_DIR"
  fi
else
  log "Cloning into $INSTALL_DIR"
  git clone "$REPO" "$INSTALL_DIR"
fi
chown -R "$HUE_USER:$HUE_USER" "$INSTALL_DIR" 2>/dev/null || true
cd "$INSTALL_DIR"

head "System Setup"
bash setup/02-finalize.sh

echo ""
log "Installation complete — HueMedia will start on next boot"