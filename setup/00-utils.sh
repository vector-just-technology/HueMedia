#!/bin/bash
# Shared utilities for setup scripts

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[x]${NC} $1"; }
head() { echo -e "\n${CYAN}=== $1 ===${NC}"; }

HUE_USER="hue"
HUE_HOME="/home/${HUE_USER}"
INSTALL_DIR="/opt/hue-media"

has_cmd() { command -v "$1" &>/dev/null; }

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    err "Must run as root"
    exit 1
  fi
}

ensure_user() {
  if ! id "$HUE_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$HUE_USER"
    usermod -aG audio,video,input,gpio,i2c,spi "$HUE_USER"
  fi
}

is_raspberry_pi() {
  [ -f /proc/device-tree/model ] && grep -qi "raspberry pi" /proc/device-tree/model
}

apt_install() {
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$@"
}

pip_install() {
  pip3 install --quiet "$@"
}

run_as_hue() {
  sudo -u "$HUE_USER" "$@"
}
