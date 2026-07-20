#!/bin/bash
# Auto-detect and mount USB storage for music library
# Called by udev rule on device add/remove

MUSIC_BASE="/mnt/music"
POOL_PATH="/pool/Music"
LOGFILE="/var/log/hue-storage.log"

log() { echo "[$(date)] $1" >> "$LOGFILE"; }

ensure_dirs() {
  mkdir -p "$MUSIC_BASE" "$POOL_PATH"
}

mount_all() {
  local mounted=0
  
  for dev in /dev/sd[a-z][0-9]; do
    [ -b "$dev" ] || continue
    
    mountpoint=$(findmnt -n -o TARGET "$dev" 2>/dev/null)
    if [ -n "$mountpoint" ]; then
      continue
    fi
    
    label=$(blkid -s LABEL -o value "$dev" 2>/dev/null || echo "usb-$(basename $dev)")
    fstype=$(blkid -s TYPE -o value "$dev" 2>/dev/null || echo "vfat")
    mnt="$MUSIC_BASE/$label"
    
    mkdir -p "$mnt"
    
    opts=""
    case "$fstype" in
      vfat|exfat|ntfs) opts="-o uid=1000,gid=1000,umask=000,noatime" ;;
      ext[234]|btrfs)  opts="-o noatime" ;;
      *)               opts="-o uid=1000,gid=1000,umask=000" ;;
    esac
    
    if mount -t "$fstype" "$dev" "$mnt" $opts 2>/dev/null; then
      log "Mounted $dev ($label) at $mnt"
      mounted=1
    else
      log "Failed to mount $dev at $mnt"
    fi
  done
  
  return $mounted
}

rebuild_pool() {
  if ! command -v mergerfs &>/dev/null; then
    return
  fi
  
  local branches=""
  
  # Each USB drive root: $MUSIC_BASE/<label>
  for mnt in "$MUSIC_BASE"/*; do
    [ -d "$mnt" ] || continue
    branches="$branches:$mnt"
  done
  
  branches="${branches#:}"
  
  if [ -z "$branches" ]; then
    return
  fi
  
  if mountpoint -q "$POOL_PATH"; then
    mount -t fuse.mergerfs -o remount,defaults,allow_other,category.create=ff "$branches" "$POOL_PATH" 2>/dev/null && \
      log "Pool updated" || true
  else
    mount -t fuse.mergerfs -o defaults,allow_other,category.create=ff "$branches" "$POOL_PATH" 2>/dev/null && \
      log "Pool mounted at $POOL_PATH"
  fi
  
  chown -R hue:hue "$MUSIC_BASE" 2>/dev/null || true
  chown -R hue:hue "$POOL_PATH" 2>/dev/null || true
}

ensure_dirs
mount_all
rebuild_pool

# Signal the player to rescan library
if [ -f /tmp/hue-media-player.pid ]; then
  kill -USR1 "$(cat /tmp/hue-media-player.pid)" 2>/dev/null || true
fi
