#!/bin/bash
# Manual pool rebuild for music storage

MUSIC_BASE="/mnt/music"
POOL_PATH="/pool/Music"
LOGFILE="/var/log/hue-storage.log"

log() { echo "[$(date)] $1" >> "$LOGFILE"; }

if ! command -v mergerfs &>/dev/null; then
  echo "mergerfs not installed"
  exit 1
fi

branches=""
for mnt in "$MUSIC_BASE"/*; do
  [ -d "$mnt" ] || continue
  branches="$branches:$mnt"
done
branches="${branches#:}"

if [ -z "$branches" ]; then
  echo "No music drives found in $MUSIC_BASE"
  exit 1
fi

if mountpoint -q "$POOL_PATH"; then
  umount "$POOL_PATH" 2>/dev/null
fi

mount -t fuse.mergerfs -o defaults,allow_other,category.create=ff "$branches" "$POOL_PATH"
echo "Pool mounted: $branches -> $POOL_PATH"
log "Pool manually rebuilt"
