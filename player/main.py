#!/usr/bin/env python3
"""HueMedia — SDL2 touchscreen player for RPi 3B + 3.5" LCD.

Entry point that initializes all subsystems and runs the SDL2 UI.
"""

import os
import sys
import signal
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("hue")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HueMedia Player")
    parser.add_argument("--sdl", action="store_true", help="Use SDL2 X11 backend (desktop dev)")
    parser.add_argument("--headless", action="store_true", help="Run without display (CLI)")
    parser.add_argument("--scan", action="store_true", help="Scan library and exit")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # SDL2 environment — framebuffer by default, X11 with --sdl
    if args.sdl:
        os.environ["SDL_VIDEODRIVER"] = "x11"
        os.environ["DISPLAY"] = ":0"
    else:
        os.environ["SDL_VIDEODRIVER"] = "fbcon"
        os.environ["SDL_FBDEV"] = "/dev/fb1"

    # Write PID for external signaling (SIGUSR1 = rescan)
    Path("/tmp/hue-media-player.pid").write_text(str(os.getpid()))

    # --- Init subsystems ---
    from config import load_config
    from engine import PlaybackEngine
    from library import MusicLibrary
    from bluetooth import BluetoothManager

    cfg = load_config()
    logger.info(f"Config loaded")

    engine = PlaybackEngine()
    library = MusicLibrary()
    bt_manager = BluetoothManager()

    if library.load_cache():
        logger.info("Loaded cached library")
    library.scan()

    # Handle SIGUSR1 -> rescan
    def handle_rescan(signum, frame):
        logger.info("Rescan triggered via SIGUSR1")
        library.scan()
    signal.signal(signal.SIGUSR1, handle_rescan)

    if args.scan:
        logger.info(f"Scan complete: {len(library.get_all_tracks())} tracks")
        return

    if args.headless:
        logger.info("Headless mode — idle")
        signal.pause()
        return

    # --- SDL2 UI ---
    from ui.sdl_app import SDLDisplay, ScreenManager
    from ui.screens import NowPlayingScreen, LibraryScreen, BluetoothScreen, SettingsScreen

    disp = SDLDisplay()
    if not disp.init():
        logger.error("Failed to initialize SDL2 display")
        return 1

    sm = ScreenManager(disp, engine, library, bt_manager)
    sm.register("now_playing", NowPlayingScreen(disp, engine, library, bt_manager, sm))
    sm.register("library", LibraryScreen(disp, engine, library, bt_manager, sm))
    sm.register("bluetooth", BluetoothScreen(disp, engine, library, bt_manager, sm))
    sm.register("settings", SettingsScreen(disp, engine, library, bt_manager, sm))

    logger.info("HueMedia started — SDL2 UI")

    try:
        sm.run()
    except KeyboardInterrupt:
        pass
    finally:
        engine.cleanup()
        bt_manager.cleanup()
        logger.info("HueMedia stopped")


if __name__ == "__main__":
    sys.exit(main() or 0)
