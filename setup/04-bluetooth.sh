#!/bin/bash
# Bluetooth audio setup for A2DP headphones + AVRCP controls

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-utils.sh" 2>/dev/null || true

require_root

head "Bluetooth Audio Setup"

# ---------------------------------------------------------------
# PulseAudio Bluetooth configuration
# ---------------------------------------------------------------
cat > /etc/pulse/default.pa.d/hue-bluetooth.pa << 'PULSE'
.ifexists module-bluetooth-discover.so
load-module module-bluetooth-discover
.endif

.ifexists module-bluetooth-policy.so
load-module module-bluetooth-policy
.endif

.ifexists module-switch-on-connect.so
load-module module-switch-on-connect
.endif
PULSE

# ---------------------------------------------------------------
# Bluetooth daemon tweaks for A2DP and AVRCP
# ---------------------------------------------------------------
cat > /etc/bluetooth/main.conf << 'BT'
[General]
Name = HueMedia
Class = 0x200414
DiscoverableTimeout = 0
PairableTimeout = 0
AutoEnable = true

[Policy]
AutoEnable = true
ReconnectUUIDs = 0000110e-0000-1000-8000-00805f9b34fb;0000110b-0000-1000-8000-00805f9b34fb
ReconnectAttempts = 10
ReconnectIntervals = 1,2,4,8,16,32,64

[GATT]
Cache = no

[AVRCP]
VolumeControl = true
PlayerApplicationSettings = true
AbsoluteVolume = true
BT

# ---------------------------------------------------------------
# Bluetooth agent for auto-pairing
# ---------------------------------------------------------------
cat > /opt/hue-media/scripts/bt-agent.sh << 'SCRIPT'
#!/bin/bash
# Simple Bluetooth agent for auto-accepting pairings
while true; do
  bluetoothctl --agent=DisplayYesNo <<< "default-agent" &>/dev/null
  bluetoothctl --agent=DisplayYesNo <<< "scan on" &>/dev/null
  sleep 60
done
SCRIPT
chmod +x /opt/hue-media/scripts/bt-agent.sh

# ---------------------------------------------------------------
# Systemd service for persistent Bluetooth
# ---------------------------------------------------------------
cat > /etc/systemd/system/hue-bluetooth.service << 'SERVICE'
[Unit]
Description=HueMedia Bluetooth Manager
After=bluetooth.target pulseaudio.service
Requires=bluetooth.target

[Service]
Type=simple
User=hue
ExecStartPre=/usr/bin/bluetoothctl -- power on
ExecStart=/opt/hue-media/player/.venv/bin/python /opt/hue-media/player/bluetooth.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICE

# Restart Bluetooth with new config
systemctl restart bluetooth
systemctl enable hue-bluetooth.service

log "Bluetooth configured — headphones will auto-connect"
log "Device name: HueMedia"
