"""Bluetooth manager — device discovery, pairing, AVRCP control."""

import logging
import threading
import subprocess
import re
import time
from typing import List, Optional, Callable
from pathlib import Path
import json

logger = logging.getLogger("bluetooth")


class BluetoothManager:
    def __init__(self):
        self._devices = []
        self._connected = None
        self._scanning = False
        self._listeners = []
        self._running = True
        self._start_monitor()

    def add_listener(self, cb: Callable):
        self._listeners.append(cb)

    def _notify(self):
        for cb in self._listeners:
            try:
                cb(self.get_status())
            except Exception:
                pass

    def get_status(self):
        return {
            "available": self._devices,
            "connected": self._connected,
            "scanning": self._scanning,
        }

    def _start_monitor(self):
        def _monitor():
            while self._running:
                self._refresh_devices()
                time.sleep(3)

        threading.Thread(target=_monitor, daemon=True).start()

    def _refresh_devices(self):
        try:
            result = subprocess.run(
                ["bluetoothctl", "--", "devices"],
                capture_output=True, text=True, timeout=5
            )
            devices = []
            for line in result.stdout.splitlines():
                m = re.match(r"Device\s+(\S+)\s+(.+)", line)
                if m:
                    mac = m.group(1)
                    name = m.group(2).strip()
                    devices.append({"mac": mac, "name": name})

            self._devices = devices

            # Check connected device via bluetoothctl info
            result = subprocess.run(
                ["bluetoothctl", "--", "info"],
                capture_output=True, text=True, timeout=5
            )
            connected = None
            stdout = result.stdout
            if "Connected: yes" in stdout:
                # Extract MAC from info output
                m = re.search(r"Device\s+(\S+)", stdout)
                if m:
                    info_mac = m.group(1)
                    for d in devices:
                        if d["mac"] == info_mac or d["mac"].replace(":", "") == info_mac.replace(":", ""):
                            connected = d
                            break
                    if not connected:
                        connected = {"mac": info_mac, "name": "Unknown"}
            self._connected = connected
            self._notify()
        except Exception as e:
            logger.error(f"BT refresh error: {e}")

    def start_scan(self):
        try:
            subprocess.run(
                ["bluetoothctl", "--", "scan", "on"],
                capture_output=True, timeout=2
            )
            self._scanning = True
            self._notify()
        except Exception as e:
            logger.error(f"Scan start error: {e}")

    def stop_scan(self):
        try:
            subprocess.run(
                ["bluetoothctl", "--", "scan", "off"],
                capture_output=True, timeout=2
            )
            self._scanning = False
            self._notify()
        except Exception as e:
            logger.error(f"Scan stop error: {e}")

    def pair(self, mac: str):
        try:
            subprocess.run(
                ["bluetoothctl", "--", "pair", mac],
                capture_output=True, timeout=15
            )
            subprocess.run(
                ["bluetoothctl", "--", "trust", mac],
                capture_output=True, timeout=5
            )
            subprocess.run(
                ["bluetoothctl", "--", "connect", mac],
                capture_output=True, timeout=15
            )
        except Exception as e:
            logger.error(f"Pair error: {e}")

    def connect(self, mac: str):
        try:
            subprocess.run(
                ["bluetoothctl", "--", "connect", mac],
                capture_output=True, timeout=15
            )
        except Exception as e:
            logger.error(f"Connect error: {e}")

    def disconnect(self):
        if self._connected:
            try:
                subprocess.run(
                    ["bluetoothctl", "--", "disconnect", self._connected["mac"]],
                    capture_output=True, timeout=10
                )
            except Exception as e:
                logger.error(f"Disconnect error: {e}")

    def forget(self, mac: str):
        try:
            subprocess.run(
                ["bluetoothctl", "--", "remove", mac],
                capture_output=True, timeout=10
            )
        except Exception as e:
            logger.error(f"Remove error: {e}")

    def cleanup(self):
        self._running = False
