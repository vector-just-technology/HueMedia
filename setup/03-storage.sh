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

# Auto-mount script
cat > /opt/hue-media/scripts/autodetect-storage.sh << 'SCRIPT'
#!/bin/bash
MUSIC_BASE="/mnt/music"
POOL_PATH="/pool/Music"
LOGFILE="/var/log/hue-storage.log"

log() { echo "[$(date)] $1" >> "$LOGFILE"; }

mkdir -p "$MUSIC_BASE"

# Find all unmounted partitions
for dev in /dev/sd[a-z][0-9]; do
  [ -b "$dev" ] || continue
  mountpoint=$(findmnt -n -o TARGET "$dev" 2>/dev/null)
  if [ -z "$mountpoint" ]; then
    label=$(blkid -s LABEL -o value "$dev" 2>/dev/null || echo "usb-$(basename $dev)")
    mnt="$MUSIC_BASE/$label"
    mkdir -p "$mnt"
    
    fstype=$(blkid -s TYPE -o value "$dev" 2>/dev/null)
    opts=""
    case "$fstype" in
      vfat)  opts="-o uid=1000,gid=1000,umask=000,shortname=mixed" ;;
      exfat) opts="-o uid=1000,gid=1000,umask=000" ;;
      ntfs)  opts="-o uid=1000,gid=1000,umask=000" ;;
      *)     opts="-o uid=1000,gid=1000,umask=000" ;;
    esac
    
    mount "$dev" "$mnt" $opts 2>/dev/null && log "Mounted $dev at $mnt"
  fi
done

# Rebuild mergerfs pool
if command -v mergerfs &>/dev/null; then
  # Find all subdirectories that contain Music/
  BRANCHES=""
  for mnt in "$MUSIC_BASE"/*; do
    [ -d "$mnt" ] || continue
    music_dir="$mnt/Music"
    if [ -d "$music_dir" ]; then
      BRANCHES="$BRANCHES:$music_dir"
    fi
    BRANCHES="$BRANCHES:$mnt"
  done
  BRANCHES="${BRANCHES#:}"
  
  if [ -n "$BRANCHES" ]; then
    if mountpoint -q "$POOL_PATH"; then
      mount -t fuse.mergerfs -o remount,defaults,allow_other,category.create=ff "$BRANCHES" "$POOL_PATH" 2>/dev/null || true
    else
      mount -t fuse.mergerfs -o defaults,allow_other,category.create=ff "$BRANCHES" "$POOL_PATH" 2>/dev/null && log "Pool mounted at $POOL_PATH"
    fi
  fi
fi

# Fix permissions
chown -R 1000:1000 "$MUSIC_BASE" 2>/dev/null || true
chown -R 1000:1000 "$POOL_PATH" 2>/dev/null || true
SCRIPT
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
