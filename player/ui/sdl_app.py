"""HueMedia SDL2 touchscreen player — initialization, event loop, screen manager."""

import os
import sys
import time
import signal
import logging
from pathlib import Path

import sdl2
import sdl2.ext
import sdl2.sdlttf as sdlttf
import sdl2.sdlimage as sdlimg

logger = logging.getLogger("ui.sdl")

WIDTH, HEIGHT = 480, 320
FPS = 30

# Colors
BG_DARK      = sdl2.SDL_Color(15, 15, 26)
BG_CARD      = sdl2.SDL_Color(26, 26, 46)
BG_HEADER    = sdl2.SDL_Color(13, 13, 32)
ACCENT       = sdl2.SDL_Color(139, 92, 246)
ACCENT2      = sdl2.SDL_Color(59, 130, 246)
TEXT_WHITE   = sdl2.SDL_Color(224, 224, 224)
TEXT_MUTED   = sdl2.SDL_Color(136, 136, 136)
TEXT_RED     = sdl2.SDL_Color(239, 68, 68)
GREEN        = sdl2.SDL_Color(34, 197, 94)
PROGRESS_BG  = sdl2.SDL_Color(42, 42, 62)
PRESSED_BG   = sdl2.SDL_Color(42, 42, 78)
TRANSPARENT  = sdl2.SDL_Color(0, 0, 0, 0)


class SDLDisplay:
    def __init__(self):
        self.window = None
        self.renderer = None
        self.font_12 = None
        self.font_14 = None
        self.font_16 = None
        self.font_20 = None
        self.running = False
        self.clock = 0
        self.last_tick = 0

    def init(self):
        sdl2.SDL_SetHint(b"SDL_FBDEV", os.environ.get("SDL_FBDEV", "/dev/fb1").encode())
        sdl2.SDL_SetHint(b"SDL_MOUSEDRV", os.environ.get("SDL_MOUSEDRV", "evdev").encode())
        sdl2.SDL_SetHint(b"SDL_MOUSEDEV", os.environ.get("SDL_MOUSEDEV", "/dev/input/touchscreen").encode())

        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_EVENTS | sdl2.SDL_INIT_TIMER) < 0:
            logger.error(f"SDL_Init failed: {sdl2.SDL_GetError()}")
            return False

        self.window = sdl2.SDL_CreateWindow(
            b"HueMedia",
            sdl2.SDL_WINDOWPOS_UNDEFINED,
            sdl2.SDL_WINDOWPOS_UNDEFINED,
            WIDTH, HEIGHT,
            sdl2.SDL_WINDOW_FULLSCREEN | sdl2.SDL_WINDOW_ALWAYS_ON_TOP
        )
        if not self.window:
            logger.error(f"SDL_CreateWindow failed: {sdl2.SDL_GetError()}")
            return False

        self.renderer = sdl2.SDL_CreateRenderer(
            self.window, -1,
            sdl2.SDL_RENDERER_SOFTWARE | sdl2.SDL_RENDERER_PRESENTVSYNC
        )
        if not self.renderer:
            logger.error(f"SDL_CreateRenderer failed: {sdl2.SDL_GetError()}")
            return False

        sdl2.SDL_ShowCursor(0)

        # Init font subsystem
        if sdlttf.TTF_Init() < 0:
            logger.error(f"TTF_Init failed: {sdlttf.TTF_GetError()}")
            return False

        # Find a font
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]
        chosen = None
        for fp in font_paths:
            if Path(fp).exists():
                chosen = fp.encode()
                break
        if not chosen:
            logger.warning("No TTF font found — text will be limited")
        else:
            self.font_12 = sdlttf.TTF_OpenFont(chosen, 12)
            self.font_14 = sdlttf.TTF_OpenFont(chosen, 14)
            self.font_16 = sdlttf.TTF_OpenFont(chosen, 16)
            self.font_20 = sdlttf.TTF_OpenFont(chosen, 20)
            logger.info(f"Loaded font: {chosen.decode()}")

        self.running = True
        self.last_tick = sdl2.SDL_GetTicks()
        return True

    def begin_frame(self):
        sdl2.SDL_SetRenderDrawColor(self.renderer, BG_DARK.r, BG_DARK.g, BG_DARK.b, 255)
        sdl2.SDL_RenderClear(self.renderer)
        now = sdl2.SDL_GetTicks()
        dt = now - self.last_tick
        self.last_tick = now
        self.clock += dt
        return dt

    def end_frame(self):
        sdl2.SDL_RenderPresent(self.renderer)
        # Cap at ~30 FPS
        elapsed = sdl2.SDL_GetTicks() - self.last_tick
        if elapsed < (1000 // FPS):
            sdl2.SDL_Delay((1000 // FPS) - elapsed)

    def render_rect(self, x, y, w, h, color, radius=0):
        rect = sdl2.SDL_Rect(x, y, w, h)
        sdl2.SDL_SetRenderDrawColor(self.renderer, color.r, color.g, color.b, 255)
        if radius > 0:
            self._rounded_rect(rect, radius)
        else:
            sdl2.SDL_RenderFillRect(self.renderer, rect)

    def _rounded_rect(self, rect, r):
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
        # Draw filled rect, then corners (approximate)
        inner = sdl2.SDL_Rect(x + r, y, w - 2 * r, h)
        sdl2.SDL_RenderFillRect(self.renderer, inner)
        inner = sdl2.SDL_Rect(x, y + r, w, h - 2 * r)
        sdl2.SDL_RenderFillRect(self.renderer, inner)
        # Quarter circles for corners
        for cx, cy in [(x + r, y + r), (x + w - r - 1, y + r),
                       (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)]:
            for dy in range(-r, r):
                for dx in range(-r, r):
                    if dx * dx + dy * dy <= r * r:
                        px, py = cx + dx, cy + dy
                        if x <= px < x + w and y <= py < y + h:
                            sdl2.SDL_RenderDrawPoint(self.renderer, px, py)

    def render_text(self, text, x, y, color, font=None, center_x=False, center_y=False):
        if font is None:
            font = self.font_14
        if font is None or not text:
            return 0, 0

        try:
            surf = sdlttf.TTF_RenderUTF8_Blended(font, text.encode(), color)
        except Exception:
            try:
                surf = sdlttf.TTF_RenderText_Blended(font, text.encode(), color)
            except Exception:
                return 0, 0

        if not surf:
            return 0, 0

        tex = sdl2.SDL_CreateTextureFromSurface(self.renderer, surf)
        if not tex:
            sdl2.SDL_FreeSurface(surf)
            return 0, 0

        tw, th = surf.contents.w, surf.contents.h
        rx, ry = x, y
        if center_x:
            rx = x - tw // 2
        if center_y:
            ry = y - th // 2

        dst = sdl2.SDL_Rect(rx, ry, tw, th)
        sdl2.SDL_RenderCopy(self.renderer, tex, None, dst)
        sdl2.SDL_DestroyTexture(tex)
        sdl2.SDL_FreeSurface(surf)
        return tw, th

    def render_texture(self, tex, x, y, w=None, h=None):
        if not tex:
            return
        dst = sdl2.SDL_Rect(x, y, w or 0, h or 0)
        sdl2.SDL_RenderCopy(self.renderer, tex, None, dst)

    def render_line(self, x1, y1, x2, y2, color, width=1):
        sdl2.SDL_SetRenderDrawColor(self.renderer, color.r, color.g, color.b, 255)
        for i in range(width):
            sdl2.SDL_RenderDrawLine(self.renderer, x1, y1 + i, x2, y2 + i)

    def fill(self, color):
        sdl2.SDL_SetRenderDrawColor(self.renderer, color.r, color.g, color.b, 255)
        sdl2.SDL_RenderClear(self.renderer)

    def poll_events(self):
        events = []
        ev = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(ev):
            etype = ev.type
            if etype == sdl2.SDL_QUIT:
                self.running = False
            elif etype == sdl2.SDL_FINGERDOWN:
                events.append({
                    "type": "touch",
                    "action": "down",
                    "x": int(ev.tfinger.x * WIDTH),
                    "y": int(ev.tfinger.y * HEIGHT),
                    "finger_id": ev.tfinger.fingerId,
                })
            elif etype == sdl2.SDL_FINGERUP:
                events.append({
                    "type": "touch",
                    "action": "up",
                    "x": int(ev.tfinger.x * WIDTH),
                    "y": int(ev.tfinger.y * HEIGHT),
                    "finger_id": ev.tfinger.fingerId,
                })
            elif etype == sdl2.SDL_FINGERMOTION:
                events.append({
                    "type": "touch",
                    "action": "move",
                    "x": int(ev.tfinger.x * WIDTH),
                    "y": int(ev.tfinger.y * HEIGHT),
                    "finger_id": ev.tfinger.fingerId,
                })
            elif etype == sdl2.SDL_MOUSEBUTTONDOWN:
                events.append({
                    "type": "mouse",
                    "action": "down",
                    "x": ev.button.x,
                    "y": ev.button.y,
                    "button": ev.button.button,
                })
            elif etype == sdl2.SDL_MOUSEBUTTONUP:
                events.append({
                    "type": "mouse",
                    "action": "up",
                    "x": ev.button.x,
                    "y": ev.button.y,
                    "button": ev.button.button,
                })
            elif etype == sdl2.SDL_KEYDOWN:
                events.append({
                    "type": "key",
                    "action": "down",
                    "key": ev.key.keysym.sym,
                })
        return events

    def cleanup(self):
        if self.font_20:
            sdlttf.TTF_CloseFont(self.font_20)
        if self.font_16:
            sdlttf.TTF_CloseFont(self.font_16)
        if self.font_14:
            sdlttf.TTF_CloseFont(self.font_14)
        if self.font_12:
            sdlttf.TTF_CloseFont(self.font_12)
        sdlttf.TTF_Quit()
        if self.renderer:
            sdl2.SDL_DestroyRenderer(self.renderer)
        if self.window:
            sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()


class ScreenManager:
    def __init__(self, display, engine, library, bt_manager):
        self.disp = display
        self.engine = engine
        self.library = library
        self.bt = bt_manager
        self.screens = {}
        self.current_name = None
        self.current = None
        self.prev_name = None

        # Tab bar
        self.tabs = [
            ("now_playing", "\u266B", "Now"),
            ("library", "\u2630", "Library"),
            ("bluetooth", "\u2248", "BT"),
            ("settings", "\u2699", "Set"),
        ]
        self.tab_w = WIDTH // len(self.tabs)
        self.tab_h = 32
        self.tab_y = HEIGHT - self.tab_h
        self.content_h = self.tab_y

    def register(self, name, screen):
        self.screens[name] = screen

    def switch(self, name):
        if name in self.screens and name != self.current_name:
            self.prev_name = self.current_name
            self.current_name = name
            self.current = self.screens[name]
            self.current.on_show()

    def handle_event(self, ev):
        if ev["type"] in ("touch", "mouse") and ev["action"] == "down":
            x, y = ev["x"], ev["y"]
            if y >= self.tab_y:
                tab_idx = x // self.tab_w
                if 0 <= tab_idx < len(self.tabs):
                    self.switch(self.tabs[tab_idx][0])
                return

        if self.current:
            self.current.handle_event(ev)

    def render(self):
        self.disp.fill(BG_DARK)

        if self.current:
            self.current.render()

        # Tab bar
        self.disp.render_rect(0, self.tab_y, WIDTH, self.tab_h, BG_HEADER)
        self.disp.render_line(0, self.tab_y, WIDTH, self.tab_y, PROGRESS_BG, 1)

        for i, (name, icon, label) in enumerate(self.tabs):
            active = name == self.current_name
            x = i * self.tab_w
            color = ACCENT if active else TEXT_MUTED
            self.disp.render_rect(x + 4, self.tab_y + 2, self.tab_w - 8, self.tab_h - 4,
                                  BG_CARD if active else TRANSPARENT, 4)
            self.disp.render_text(icon, x + self.tab_w // 2, self.tab_y + 6,
                                  color, self.disp.font_14, center_x=True)
            self.disp.render_text(label, x + self.tab_w // 2, self.tab_y + self.tab_h - 10,
                                  color, self.disp.font_12, center_x=True)

    def run(self):
        if not self.disp.running:
            return

        logger.info("SDL2 UI starting")

        # Switch to initial screen
        if self.current_name is None and self.screens:
            self.switch(list(self.screens.keys())[0])

        while self.disp.running:
            self.disp.begin_frame()

            # Poll events
            for ev in self.disp.poll_events():
                if ev["type"] == "key" and ev["key"] == sdl2.SDLK_ESCAPE:
                    self.disp.running = False
                self.handle_event(ev)

            # Render
            self.render()
            self.disp.end_frame()

            # Update display every frame
            if self.current:
                self.current.tick()

        self.disp.cleanup()
        logger.info("SDL2 UI stopped")
