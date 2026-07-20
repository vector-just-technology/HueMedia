#!/usr/bin/env python3
"""HueMedia — LVGL touchscreen player for RPi 3B + 3.5" LCD.

Entry point that initializes all subsystems and runs the UI.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("hue")


def main():
    parser = argparse.ArgumentParser(description="HueMedia Player")
    parser.add_argument("--sdl", action="store_true", help="Use SDL2 backend (for development)")
    parser.add_argument("--headless", action="store_true", help="Run without display (CLI mode)")
    parser.add_argument("--scan", action="store_true", help="Scan library and exit")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set environment for SDL/FB
    if args.sdl:
        os.environ.setdefault("SDL_VIDEODRIVER", "x11")
    else:
        os.environ.setdefault("SDL_FBDEV", "/dev/fb1")
        os.environ.setdefault("SDL_MOUSEDEV", "/dev/input/touchscreen")
        os.environ.setdefault("SDL_MOUSEDRV", "evdev")
        os.environ.setdefault("SDL_VIDEODRIVER", "fbcon")

    # Write PID file for signaling
    Path("/tmp/hue-media-player.pid").write_text(str(os.getpid()))

    # --- Init subsystems ---
    from config import load_config, save_config
    from engine import PlaybackEngine
    from library import MusicLibrary
    from bluetooth import BluetoothManager

    cfg = load_config()
    logger.info(f"Config loaded: volume={cfg.get('volume')}, shuffle={cfg.get('shuffle')}")

    engine = PlaybackEngine()
    library = MusicLibrary()
    bt_manager = BluetoothManager()

    # Try loading cached library, then scan in background
    if library.load_cache():
        logger.info("Loaded library from cache")
    library.scan()

    # --- Init display ---
    from ui.app import DisplayDriver, ScreenManager
    from ui.now_playing import NowPlayingScreen
    from ui.library import LibraryScreen
    from ui.bluetooth import BluetoothScreen
    from ui.settings import SettingsScreen

    disp = DisplayDriver(sdl_mode=args.sdl)
    disp.init()

    sm = ScreenManager(engine, library, bt_manager, disp)

    # Register screens
    sm.register("now_playing", NowPlayingScreen(engine, library))
    sm.register("library", LibraryScreen(engine, library, sm))
    sm.register("bluetooth", BluetoothScreen(engine, bt_manager))
    sm.register("settings", SettingsScreen(engine, library, disp, bt_manager))

    # Handle SIGUSR1 -> rescan library
    import signal as sig

    def handle_rescan(signum, frame):
        logger.info("Rescanning library...")
        library.scan()

    sig.signal(sig.SIGUSR1, handle_rescan)

    # Switch to now-playing screen
    sm.switch("now_playing")

    logger.info("HueMedia started")

    if args.scan:
        logger.info("Scan complete — exiting")
        return

    # Run UI loop
    try:
        sm.run()
    except KeyboardInterrupt:
        pass
    finally:
        engine.cleanup()
        bt_manager.cleanup()
        logger.info("HueMedia stopped")


if __name__ == "__main__":
    main()
