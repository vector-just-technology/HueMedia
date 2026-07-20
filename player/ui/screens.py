"""HueMedia SDL2 screens — Now Playing, Library, Bluetooth, Settings."""

import os
import subprocess
import logging
from pathlib import Path

import sdl2

from sdl_app import (
    WIDTH, HEIGHT, BG_DARK, BG_CARD, BG_HEADER, ACCENT, ACCENT2,
    TEXT_WHITE, TEXT_MUTED, TEXT_RED, GREEN, PROGRESS_BG, PRESSED_BG, TRANSPARENT
)
from widgets import BaseScreen, Button, Slider, CoverArt

logger = logging.getLogger("ui.screens")


class NowPlayingScreen(BaseScreen):
    def __init__(self, disp, engine, library, bt_manager, sm):
        super().__init__(disp, engine, library, bt_manager, sm)
        self.cover = CoverArt(140, 28, 200)
        self.play_btn = Button(210, 268, 60, 44, "", self._toggle, ACCENT, disp.font_20, 22)
        self.play_btn.icon = "\u25B6"
        self.prev_btn = Button(78, 275, 52, 36, "\u23EE", engine.previous, BG_CARD, disp.font_16)
        self.next_btn = Button(350, 275, 52, 36, "\u23ED", engine.next, BG_CARD, disp.font_16)
        vol = engine.get_status().get("volume", 50)
        self.volume_slider = Slider(370, 12, 100, 4, 0, 100, vol)
        self.progress_slider = None
        self.repeat_btn = Button(10, 275, 50, 36, "", engine.cycle_repeat, BG_CARD, disp.font_14)
        self.shuffle_btn = Button(420, 275, 50, 36, "", engine.toggle_shuffle, BG_CARD, disp.font_14)
        self._update_icons()

    def _update_icons(self):
        cfg = self.engine.get_status()
        rpt = cfg.get("repeat", "off")
        if rpt == "off":
            self.repeat_btn.icon = "\u21BB"
            self.repeat_btn.color = BG_CARD
        elif rpt == "all":
            self.repeat_btn.icon = "\u21BB"
            self.repeat_btn.color = ACCENT
        else:
            self.repeat_btn.icon = "1"
            self.repeat_btn.color = ACCENT

        shf = cfg.get("shuffle", False)
        self.shuffle_btn.icon = "\u21C4"
        self.shuffle_btn.color = ACCENT if shf else BG_CARD

    def _toggle(self):
        self.engine.toggle_pause()
        s = self.engine.get_status()
        self.play_btn.icon = "\u23F8" if s.get("state") == "playing" else "\u25B6"

    def tick(self):
        s = self.engine.get_status()
        track = s.get("current")
        if track:
            self.cover.load(track.get("cover"), self.disp.renderer)
        self.volume_slider.value = s.get("volume", 50)
        self._update_icons()

    def handle_event(self, ev):
        if ev["action"] == "down":
            x, y = ev["x"], ev["y"]
            for btn in [self.play_btn, self.prev_btn, self.next_btn, self.repeat_btn, self.shuffle_btn]:
                if btn.hit_test(x, y):
                    btn.pressed = True
            if self.volume_slider.hit_test(x, y):
                self.volume_slider.dragging = True

        elif ev["action"] == "up":
            x, y = ev["x"], ev["y"]
            for btn in [self.play_btn, self.prev_btn, self.next_btn, self.repeat_btn, self.shuffle_btn]:
                if btn.pressed and btn.hit_test(x, y) and btn.callback:
                    btn.callback()
                    self._update_icons()
                    self.play_btn.icon = "\u23F8" if self.engine.get_status().get("state")=="playing" else "\u25B6"
                btn.pressed = False

            if self.volume_slider.dragging:
                self.volume_slider.dragging = False
                self.volume_slider.set_from_x(x)
                self.engine.set_volume(int(self.volume_slider.value))

        elif ev["action"] == "move":
            if self.volume_slider.dragging:
                self.volume_slider.set_from_x(ev["x"])

    def render(self):
        s = self.engine.get_status()
        track = s.get("current")

        self.volume_slider.render(self.disp, ACCENT2)
        vol_label = str(int(s.get("volume", 50)))
        self.disp.render_text(vol_label, WIDTH - 20, 4, TEXT_MUTED, self.disp.font_12)

        self.cover.render(self.disp)

        if track:
            self.disp.render_text(track.get("artist", ""), WIDTH // 2, 8, TEXT_MUTED, self.disp.font_12, center_x=True)

            title = track.get("title", "")
            self.disp.render_text(title, WIDTH // 2, 232, TEXT_WHITE, self.disp.font_16, center_x=True)

            pos = s.get("position", 0)
            dur = s.get("duration", 0)
            if dur > 0:
                ratio = pos / dur
                bar_x, bar_y, bar_w = 40, 254, 400
                self.disp.render_rect(bar_x, bar_y, bar_w, 4, PROGRESS_BG, 2)
                fill_w = int(ratio * bar_w)
                if fill_w > 0:
                    self.disp.render_rect(bar_x, bar_y, fill_w, 4, ACCENT, 2)

            def fmt(s):
                m, sec = divmod(int(s), 60)
                return f"{m}:{sec:02d}"
            time_str = f"{fmt(pos)} / {fmt(dur)}"
            self.disp.render_text(time_str, WIDTH // 2, 262, TEXT_MUTED, self.disp.font_12, center_x=True)
        else:
            self.disp.render_text("No track playing", WIDTH // 2, 240, TEXT_MUTED, self.disp.font_14, center_x=True)
            self.disp.render_text("Browse Library or add music via SAMBA", WIDTH // 2, 260, TEXT_MUTED, self.disp.font_12, center_x=True)

        self.prev_btn.render(self.disp)
        self.play_btn.render(self.disp)
        self.next_btn.render(self.disp)
        self.repeat_btn.render(self.disp)
        self.shuffle_btn.render(self.disp)

        self.disp.render_line(0, HEIGHT - 33, WIDTH, HEIGHT - 33, PROGRESS_BG, 1)


class LibraryScreen(BaseScreen):
    def __init__(self, disp, engine, library, bt_manager, sm):
        super().__init__(disp, engine, library, bt_manager, sm)
        self.artists = []
        self.selected_artist = None
        self.songs = []
        self.scroll_y = 0
        self.item_h = 42
        self.max_visible = (HEIGHT - 64) // self.item_h
        self.lib_y = 36
        self.lib_h = HEIGHT - 36 - 33
        self.touch_start_y = 0
        self.scroll_start_y = 0
        self.dragging = False

    def on_show(self):
        self.artists = self.library.get_artists()
        self.selected_artist = None
        self.scroll_y = 0

    def handle_event(self, ev):
        if ev["action"] == "down":
            x, y = ev["x"], ev["y"]
            if y < 36:
                if self.selected_artist:
                    self.selected_artist = None
                    self.scroll_y = 0
                return
            if y >= HEIGHT - 33:
                return

            self.touch_start_y = y
            self.scroll_start_y = self.scroll_y
            self.dragging = True

            items = self.songs if self.selected_artist else self.artists
            idx = (y - self.lib_y + self.scroll_y) // self.item_h
            if 0 <= idx < len(items):
                if not self.selected_artist:
                    if idx < len(self.artists):
                        self.selected_artist = self.artists[idx]
                        self.scroll_y = 0
                        self._load_songs()
                else:
                    if idx < len(self.songs):
                        self.engine.play(self.songs[idx])

        elif ev["action"] == "move" and self.dragging:
            dy = self.touch_start_y - ev["y"]
            self.scroll_y = max(0, self.scroll_start_y + dy)

        elif ev["action"] == "up":
            self.dragging = False

    def _load_songs(self):
        if self.selected_artist:
            self.songs = self.selected_artist.get("songs", [])

    def render(self):
        self.disp.render_rect(0, 0, WIDTH, 36, BG_HEADER)
        title = self.selected_artist["name"] if self.selected_artist else "Library"
        self.disp.render_text(title, WIDTH // 2, 10, TEXT_WHITE, self.disp.font_16, center_x=True)
        if self.selected_artist:
            self.disp.render_text("\u2190", 20, 8, ACCENT, self.disp.font_16)

        items = self.songs if self.selected_artist else self.artists
        if not items:
            self.disp.render_text("No music found", WIDTH // 2, HEIGHT // 2, TEXT_MUTED, self.disp.font_14, center_x=True)
            self.disp.render_text("Add via SAMBA: \\\\10.0.0.174\\MUSIC", WIDTH // 2, HEIGHT // 2 + 20, TEXT_MUTED, self.disp.font_12, center_x=True)
            return

        start_idx = max(0, self.scroll_y // self.item_h)
        for i in range(start_idx, min(len(items), start_idx + self.max_visible + 2)):
            item = items[i]
            y = self.lib_y + i * self.item_h - self.scroll_y
            if y < self.lib_y - self.item_h or y > self.lib_y + self.lib_h:
                continue

            odd = i % 2
            bg = sdl2.SDL_Color(20, 20, 36) if odd else sdl2.SDL_Color(26, 26, 46)
            self.disp.render_rect(8, y, WIDTH - 16, self.item_h - 4, bg, 6)

            if self.selected_artist:
                name = item.get("title", "")
                self.disp.render_text(name, 20, y + (self.item_h - 4) // 2, TEXT_WHITE, self.disp.font_14, center_y=True)
            else:
                artist = item if isinstance(item, dict) else {"name": str(item), "count": 0}
                name = artist.get("name", "")
                count = artist.get("count", 0)
                self.disp.render_text(name, 20, y + (self.item_h - 4) // 2 - 4, TEXT_WHITE, self.disp.font_14, center_y=True)
                self.disp.render_text(f"{count}", WIDTH - 30, y + (self.item_h - 4) // 2, TEXT_MUTED, self.disp.font_12, center_y=True)


class BluetoothScreen(BaseScreen):
    def __init__(self, disp, engine, library, bt_manager, sm):
        super().__init__(disp, engine, library, bt_manager, sm)
        self.scan_btn = Button(WIDTH - 100, 4, 90, 30, "Scan", self._scan_toggle, ACCENT, disp.font_12, 15)
        self.scroll_y = 0
        self.touch_start_y = 0
        self.scroll_start_y = 0
        self.dragging = False

    def _scan_toggle(self):
        s = self.bt.get_status()
        if s.get("scanning"):
            self.bt.stop_scan()
        else:
            self.bt.start_scan()

    def handle_event(self, ev):
        if ev["action"] == "down":
            x, y = ev["x"], ev["y"]
            if self.scan_btn.hit_test(x, y):
                self.scan_btn.pressed = True
                return
            if y < 40 or y >= HEIGHT - 33:
                return
            self.touch_start_y = y
            self.scroll_start_y = self.scroll_y
            self.dragging = True

            devices = self.bt.get_status().get("available", [])
            idx = (y - 40 + self.scroll_y) // 48
            if 0 <= idx < len(devices):
                dev = devices[idx]
                connected = self.bt.get_status().get("connected")
                if connected and connected["mac"] == dev["mac"]:
                    self.bt.disconnect()
                else:
                    self.bt.pair(dev["mac"])

        elif ev["action"] == "move" and self.dragging:
            dy = self.touch_start_y - ev["y"]
            self.scroll_y = max(0, self.scroll_start_y + dy)

        elif ev["action"] == "up":
            self.dragging = False
            self.scan_btn.pressed = False

    def render(self):
        s = self.bt.get_status()

        self.disp.render_rect(0, 0, WIDTH, 36, BG_HEADER)
        self.disp.render_text("Bluetooth", WIDTH // 2, 10, TEXT_WHITE, self.disp.font_16, center_x=True)
        self.scan_btn.color = GREEN if s.get("scanning") else ACCENT
        self.scan_btn.label = "Scanning.." if s.get("scanning") else "Scan"
        self.scan_btn.render(self.disp)

        connected = s.get("connected")
        if connected:
            self.disp.render_rect(8, 40, WIDTH - 16, 36, sdl2.SDL_Color(26, 58, 26), 8)
            self.disp.render_text("[BT]", 20, 58, GREEN, self.disp.font_14)
            self.disp.render_text(connected.get("name", ""), 44, 52, TEXT_WHITE, self.disp.font_14)
            self.disp.render_text(connected.get("mac", ""), 44, 68, TEXT_MUTED, self.disp.font_12)
        else:
            self.disp.render_text("No device connected", WIDTH // 2, 54, TEXT_MUTED, self.disp.font_14, center_x=True)

        devices = s.get("available", [])
        if not devices:
            self.disp.render_text("Tap Scan to discover devices", WIDTH // 2, 90, TEXT_MUTED, self.disp.font_12, center_x=True)
        else:
            start_y = 82
            connected_mac = connected.get("mac") if connected else None

            for i, dev in enumerate(devices):
                y = start_y + i * 48 - self.scroll_y
                if y < 80 - 48 or y > HEIGHT - 33:
                    continue

                is_conn = dev["mac"] == connected_mac
                bg = sdl2.SDL_Color(26, 58, 26) if is_conn else BG_CARD
                self.disp.render_rect(8, y, WIDTH - 16, 44, bg, 8)

                self.disp.render_text(dev.get("name", "Unknown"), 20, y + 8, TEXT_WHITE, self.disp.font_14)
                self.disp.render_text(dev.get("mac", ""), 20, y + 26, TEXT_MUTED, self.disp.font_12)

                if is_conn:
                    self.disp.render_text("Connected", WIDTH - 90, y + 14, GREEN, self.disp.font_12)


class SettingsScreen(BaseScreen):
    def __init__(self, disp, engine, library, bt_manager, sm):
        super().__init__(disp, engine, library, bt_manager, sm)
        self.scroll_y = 0
        self.touch_start_y = 0
        self.scroll_start_y = 0
        self.dragging = False
        self.items = [
            ("info", "System Info"),
            ("rescan", "Rescan Library"),
            ("reboot", "Reboot System"),
            ("shutdown", "Shutdown"),
            ("restart", "Restart Player"),
            ("version", "Version 1.0"),
        ]

    def handle_event(self, ev):
        if ev["action"] == "down":
            x, y = ev["x"], ev["y"]
            if y < 36 or y >= HEIGHT - 33:
                return

            self.touch_start_y = y
            self.scroll_start_y = self.scroll_y
            self.dragging = True

            idx = (y - 36 + self.scroll_y) // 48
            if 0 <= idx < len(self.items):
                action = self.items[idx][0]
                if action == "rescan":
                    self.library.scan()
                elif action == "reboot":
                    subprocess.Popen(["reboot"])
                elif action == "shutdown":
                    subprocess.Popen(["poweroff"])
                elif action == "restart":
                    subprocess.Popen(["systemctl", "restart", "hue-player"])

        elif ev["action"] == "move" and self.dragging:
            dy = self.touch_start_y - ev["y"]
            self.scroll_y = max(0, self.scroll_start_y + dy)

        elif ev["action"] == "up":
            self.dragging = False

    def render(self):
        self.disp.render_rect(0, 0, WIDTH, 36, BG_HEADER)
        self.disp.render_text("Settings", WIDTH // 2, 10, TEXT_WHITE, self.disp.font_16, center_x=True)

        for i, (action, label) in enumerate(self.items):
            y = 36 + i * 48 - self.scroll_y
            if y < 36 - 48 or y > HEIGHT - 33:
                continue

            is_danger = action in ("reboot", "shutdown")
            bg = sdl2.SDL_Color(60, 20, 20) if is_danger else BG_CARD
            self.disp.render_rect(8, y, WIDTH - 16, 44, bg, 8)

            color = TEXT_RED if is_danger else TEXT_WHITE
            self.disp.render_text(label, 20, y + 14, color, self.disp.font_14)
