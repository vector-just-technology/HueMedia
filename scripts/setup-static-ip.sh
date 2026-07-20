#!/bin/bash
# Sets static IP 10.0.0.174 on the first available network interface.
# Called by hue-static-ip.service on boot.

IP="10.0.0.174/24"
GW="10.0.0.1"
DNS="8.8.8.8"

# Try eth0 first, fall back to wlan0
for iface in eth0 wlan0; do
  if ip link show "$iface" &>/dev/null; then
    # Check if already has an IP in our range
    existing=$(ip -4 addr show "$iface" | grep -oP '10\.0\.0\.\d+' || true)
    if [ -n "$existing" ]; then
      exit 0
    fi

    ip addr add "$IP" dev "$iface" 2>/dev/null || true
    ip link set "$iface" up
    break
  fi
done
