#!/bin/bash
# Storage setup: auto-detect, mount, pool via mergerfs

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-utils.sh" 2>/dev/null || true

require_root

head "Storage Setup: Dual Drive + Pooling"

MUSIC_MOUNT_BASE="/mnt/music"
POOL_PATH="/pool/Music"

# Create base directories
mkdir -p "$MUSIC_MOUNT_BASE" "$POOL_PATH"

# ---------------------------------------------------------------
# udev rule for auto-mounting USB drives
# ---------------------------------------------------------------
cat > /etc/udev/rules.d/99-hue-automount.rules << 'UDEV'
ACTION=="add", KERNEL=="sd[a-z][0-9]", SUBSYSTEM=="block", ENV{ID_FS_TYPE}!="", \
  RUN+="/opt/hue-media/scripts/autodetect-storage.sh"

ACTION=="remove", KERNEL=="sd[a-z][0-9]", SUBSYSTEM=="block", \
  RUN+="/opt/hue-media/scripts/autodetect-storage.sh"
UDEV

# Auto-mount script (use repo version)
cp "$INSTALL_DIR/scripts/autodetect-storage.sh" /opt/hue-media/scripts/autodetect-storage.sh
chmod +x /opt/hue-media/scripts/autodetect-storage.sh

# Initial scan
bash /opt/hue-media/scripts/autodetect-storage.sh

# Systemd oneshot service for boot-time storage detection
cat > /etc/systemd/system/hue-automount.service << 'SERVICE'
[Unit]
Description=HueMedia Storage Auto-Detection
After=local-fs.target
Before=mergerfs.service

[Service]
Type=oneshot
ExecStart=/opt/hue-media/scripts/autodetect-storage.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE

log "Storage setup complete — drives auto-detected and pooled"
