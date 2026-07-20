"""Main LVGL application — initializes display, touch, and screen manager."""

import os
import sys
import logging
import threading
import signal
from pathlib import Path

logger = logging.getLogger("ui")

LVGL_AVAILABLE = False
try:
    import lvgl as lv
    LVGL_AVAILABLE = True
except ImportError:
    logger.warning("LVGL not available — will use debug/fallback mode")


class DisplayDriver:
    def __init__(self, width=480, height=320, sdl_mode=False):
        self.width = width
        self.height = height
        self.sdl_mode = sdl_mode

    def init(self):
        if not LVGL_AVAILABLE:
            logger.info("LVGL not available — skipping display init")
            return

        lv.init()

        if self.sdl_mode:
            self._init_sdl()
        else:
            self._init_fbdev()

    def _init_sdl(self):
        from sdl_display import SDLDisplay
        from sdl_mouse import SDLMouse
        self.disp = SDLDisplay(self.width, self.height)
        self.mouse = SDLMouse()

    def _init_fbdev(self):
        fbdev = os.environ.get("SDL_FBDEV", "/dev/fb1")
        if not Path(fbdev).exists():
            fbdev = "/dev/fb0"

        try:
            from fbdev_display import FBDevDisplay
            from evdev_mouse import EvdevMouse
            self.disp = FBDevDisplay(fbdev)
            # Find touch input device
            touch_dev = "/dev/input/touchscreen"
            if not Path(touch_dev).exists():
                for ev in sorted(Path("/dev/input").glob("event*")):
                    touch_dev = str(ev)
                    break
            self.mouse = EvdevMouse(touch_dev)
        except Exception as e:
            logger.error(f"FBDev init failed: {e}")
            self._init_sdl()


class ScreenManager:
    def __init__(self, engine, library, bt_manager, display_driver):
        self.engine = engine
        self.library = library
        self.bt_manager = bt_manager
        self.disp = display_driver
        self.screens = {}
        self.current = None

    def register(self, name, screen):
        self.screens[name] = screen

    def switch(self, name):
        if name in self.screens and LVGL_AVAILABLE:
            import lvgl as lv
            self.current = name
            screen_obj = self.screens[name].build()
            lv.scr_load(screen_obj)
            self.screens[name].on_show()

    def run(self):
        if not LVGL_AVAILABLE:
            logger.info("LVGL not available — running in headless mode")
            self._headless_loop()
            return

        import lvgl as lv
        logger.info("LVGL UI initialized — entering event loop")

        def lv_loop():
            while True:
                lv.task_handler()
                import time
                time.sleep(0.005)

        thread = threading.Thread(target=lv_loop, daemon=True)
        thread.start()

        signal.pause()

    def _headless_loop(self):
        import time
        logger.info("Headless mode — polling engine status")
        while True:
            status = self.engine.get_status()
            logger.debug(f"Status: {status.get('state')} | "
                         f"{status.get('current', {}).get('title', '')}")
            time.sleep(1)
