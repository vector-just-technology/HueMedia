"""Base screen class and widget helpers for the SDL2 player UI."""

from pathlib import Path

import sdl2
import sdl2.sdlttf as sdlttf
import sdl2.sdlimage as sdlimg

from sdl_app import (
    WIDTH, HEIGHT, BG_CARD, BG_HEADER, ACCENT, ACCENT2,
    TEXT_WHITE, TEXT_MUTED, TEXT_RED, GREEN, PROGRESS_BG, PRESSED_BG, TRANSPARENT
)


class BaseScreen:
    def __init__(self, disp, engine, library, bt_manager, sm):
        self.disp = disp
        self.engine = engine
        self.library = library
        self.bt = bt_manager
        self.sm = sm

    def on_show(self):
        pass

    def handle_event(self, ev):
        pass

    def tick(self):
        pass

    def render(self):
        pass


class Button:
    def __init__(self, x, y, w, h, label, callback=None, color=None, font=None, radius=8):
        self.rect = sdl2.SDL_Rect(int(x), int(y), int(w), int(h))
        self.label = str(label) if label else ""
        self.callback = callback
        self.color = color or ACCENT
        self.font = font
        self.radius = radius
        self.pressed = False
        self.enabled = True
        self.icon = ""

    def hit_test(self, px, py):
        r = self.rect
        return r.x <= px <= r.x + r.w and r.y <= py <= r.y + r.h

    def render(self, disp):
        if not self.enabled:
            return
        bg = PRESSED_BG if self.pressed else self.color
        disp.render_rect(self.rect.x, self.rect.y, self.rect.w, self.rect.h, bg, self.radius)

        font = self.font or disp.font_14
        text = self.icon or self.label
        if text:
            try:
                disp.render_text(text,
                                 self.rect.x + self.rect.w // 2,
                                 self.rect.y + self.rect.h // 2,
                                 TEXT_WHITE, font, center_x=True, center_y=True)
            except Exception:
                pass


class Slider:
    def __init__(self, x, y, w, h=6, min_val=0, max_val=100, value=50):
        self.rect = sdl2.SDL_Rect(int(x), int(y), int(w), int(h))
        self.min = min_val
        self.max = max_val
        self.value = value
        self.dragging = False

    def hit_test(self, px, py):
        r = self.rect
        return r.x <= px <= r.x + r.w and r.y - 15 <= py <= r.y + r.h + 15

    def set_from_x(self, x):
        r = self.rect
        ratio = max(0.0, min(1.0, (x - r.x) / max(r.w, 1)))
        self.value = self.min + ratio * (self.max - self.min)

    def render(self, disp, fill_color=None, bg_color=None):
        fill = fill_color or ACCENT
        bg = bg_color or PROGRESS_BG
        # Bar background
        disp.render_rect(self.rect.x, self.rect.y, self.rect.w, self.rect.h, bg, 3)
        # Fill
        ratio = (self.value - self.min) / max(self.max - self.min, 1)
        fill_w = max(0, int(ratio * self.rect.w))
        if fill_w > 0:
            disp.render_rect(self.rect.x, self.rect.y, fill_w, self.rect.h, fill, 3)
        # Knob
        knob_x = self.rect.x + fill_w
        knob_y = self.rect.y + self.rect.h // 2 - 5
        disp.render_rect(knob_x - 4, knob_y, 8, 10, fill, 4)


class CoverArt:
    def __init__(self, x, y, size):
        self.rect = sdl2.SDL_Rect(int(x), int(y), int(size), int(size))
        self.size = size
        self.texture = None
        self.path = None

    def load(self, filepath, renderer=None):
        if filepath == self.path and self.texture:
            return
        self.path = filepath
        self._cleanup()

        if filepath and Path(filepath).exists():
            surf = sdlimg.IMG_Load(filepath.encode("utf-8"))
            if surf:
                if renderer:
                    self.texture = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
                sdl2.SDL_FreeSurface(surf)

    def render(self, disp):
        if self.texture:
            dst = sdl2.SDL_Rect(self.rect.x, self.rect.y, self.size, self.size)
            sdl2.SDL_RenderCopy(disp.renderer, self.texture, None, dst)
        else:
            disp.render_rect(self.rect.x, self.rect.y, self.size, self.size, BG_HEADER, 8)
            try:
                disp.render_text("\u266B",
                                 self.rect.x + self.size // 2,
                                 self.rect.y + self.size // 2,
                                 TEXT_MUTED, disp.font_20, center_x=True, center_y=True)
            except Exception:
                pass

    def _cleanup(self):
        if self.texture:
            sdl2.SDL_DestroyTexture(self.texture)
            self.texture = None
