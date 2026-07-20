#!/usr/bin/env python3
"""HueMedia API Server entry point — initializes shared engine and starts Flask."""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="[api] %(levelname)s: %(message)s")
logger = logging.getLogger("api")

# Determine paths
PLAYER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PLAYER_DIR, "player"))

# Initialize shared subsystems
from engine import PlaybackEngine
from library import MusicLibrary

engine = PlaybackEngine()
library = MusicLibrary()

# Load library cache / scan
library.load_cache()
library.scan()

# Initialize Bluetooth if available
bt_manager = None
try:
    from bluetooth import BluetoothManager
    bt_manager = BluetoothManager()
except Exception as e:
    logger.warning(f"Bluetooth not available: {e}")

# Wire into main module
import main as api_main
api_main.engine = engine
api_main.library = library
api_main.bt_manager = bt_manager
api_main.player_dir = PLAYER_DIR

# Create and run app
app = api_main.create_app()

if __name__ == "__main__":
    logger.info("HueMedia API server starting on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
