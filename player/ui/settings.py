"""Settings screen — playback, display, system info."""

import logging
import subprocess

logger = logging.getLogger("ui.settings")


class SettingsScreen:
    def __init__(self, engine, library, disp, bt_manager):
        self.engine = engine
        self.library = library
        self.disp = disp
        self.bt = bt_manager
        self._screen = None
        self._list = None

    def build(self):
        if not self._lv_available():
            return None

        import lvgl as lv

        scr = lv.obj()
        scr.set_style_bg_color(lv.color_hex(0x000015), 0)

        # Header
        header = lv.obj(scr)
        header.set_size(480, 40)
        header.align(lv.ALIGN.TOP_LEFT, 0, 0)
        header.set_style_bg_color(lv.color_hex(0x0D0D20), 0)

        title = lv.label(header)
        title.set_text("Settings")
        title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        title.set_style_text_font(lv.font_montserrat_16, 0)
        title.align(lv.ALIGN.CENTER, 0, 0)

        # Scrollable list
        list_container = lv.list(scr)
        list_container.set_size(480, 280)
        list_container.align(lv.ALIGN.TOP_LEFT, 0, 40)
        list_container.set_style_bg_color(lv.color_hex(0x000015), 0)
        list_container.set_style_border_width(0, 0)
        self._list = list_container

        self._populate()

        self._screen = scr
        return scr

    def _lv_available(self):
        try:
            import lvgl
            return True
        except ImportError:
            return False

    def on_show(self):
        self._populate()

    def _populate(self):
        if not self._list:
            return

        import lvgl as lv

        self._list.clean()

        settings = [
            ("Volume", f"{self.engine.get_status().get('volume', 80)}%"),
            ("Shuffle", "On" if self.engine._shuffle else "Off"),
            ("Repeat", self.engine._repeat.upper()),
            ("Rescan Library", "Tap to rescan"),
            ("System Info", f"{self.disp.width}x{self.disp.height}"),
            ("Version", "HueMedia v1.0"),
        ]

        for setting, value in settings:
            btn = lv.btn(self._list)
            btn.set_size(460, 44)
            btn.set_style_radius(8, 0)
            btn.set_style_bg_color(lv.color_hex(0x1A1A2E), 0)
            btn.set_style_bg_color(lv.color_hex(0x2A2A4E), lv.STATE.PRESSED)
            btn.set_style_pad_left(15, 0)

            label = lv.label(btn)
            label.set_text(f"{setting}: {value}")
            label.set_style_text_color(lv.color_hex(0xDDDDDD), 0)
            label.set_style_text_font(lv.font_montserrat_14, 0)

            if setting == "Rescan Library":
                btn.add_event_cb(lambda e: self.library.scan(), lv.EVENT.CLICKED, None)

        # Action buttons
        actions = [
            ("Reboot System", "danger", lambda e: subprocess.run(["reboot"])),
            ("Shutdown", "danger", lambda e: subprocess.run(["poweroff"])),
            ("Restart Player", "secondary", lambda e: subprocess.run(["systemctl", "restart", "hue-player"])),
        ]

        for action, style, cb in actions:
            btn = lv.btn(self._list)
            btn.set_size(460, 48)
            btn.set_style_radius(8, 0)
            if style == "danger":
                btn.set_style_bg_color(lv.color_hex(0x4A1010), 0)
            else:
                btn.set_style_bg_color(lv.color_hex(0x2A2A3E), 0)
            btn.set_style_pad_left(15, 0)

            label = lv.label(btn)
            label.set_text(action)
            label.set_style_text_color(
                lv.color_hex(0xFF5555) if style == "danger" else lv.color_hex(0xDDDDDD), 0
            )
            label.set_style_text_font(lv.font_montserrat_14, 0)

            btn.add_event_cb(cb, lv.EVENT.CLICKED, None)
