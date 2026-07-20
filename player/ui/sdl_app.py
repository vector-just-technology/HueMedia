"""HueMedia SDL2 touchscreen player — initialization, event loop, screen manager."""

import os
import sys
import time
import signal
import ctypes
import logging
from pathlib import Path

import sdl2

logger = logging.getLogger("ui.sdl")

WIDTH, HEIGHT = 480, 320
FPS = 30

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

try:
    import sdl2.sdlttf as sdlttf
    _HAS_TTF = True
except ImportError:
    try:
        import sdl2.ttf as sdlttf
        _HAS_TTF = True
    except ImportError:
        sdlttf = None
        _HAS_TTF = False
        logger.warning("SDL2_ttf not available — text rendering disabled")

try:
    import sdl2.sdlimage as sdlimg
    _HAS_IMG = True
except ImportError:
    try:
        import sdl2.image as sdlimg
        _HAS_IMG = True
    except ImportError:
        sdlimg = None
        _HAS_IMG = False
        logger.warning("SDL2_image not available — cover art disabled")


def _safe_render_set_draw_color(renderer, color, a=255):
    if renderer:
        sdl2.SDL_SetRenderDrawColor(renderer, color.r, color.g, color.b, a)


def _safe_render_clear(renderer):
    if renderer:
        sdl2.SDL_RenderClear(renderer)


def _safe_render_fill_rect(renderer, rect):
    if renderer and rect:
        sdl2.SDL_RenderFillRect(renderer, rect)


def _safe_render_draw_line(renderer, x1, y1, x2, y2):
    if renderer:
        sdl2.SDL_RenderDrawLine(renderer, x1, y1, x2, y2)


def _safe_render_copy(renderer, texture, src, dst):
    if renderer and texture:
        sdl2.SDL_RenderCopy(renderer, texture, src, dst)


def _safe_render_present(renderer):
    if renderer:
        sdl2.SDL_RenderPresent(renderer)


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
        fbdev = os.environ.get("SDL_FBDEV", "/dev/fb1")
        sdl2.SDL_SetHint(b"SDL_FBDEV", fbdev.encode())

        mousedev = os.environ.get("SDL_MOUSEDEV", "")
        if not mousedev:
            for candidate in ["/dev/input/touchscreen", "/dev/input/event0", "/dev/input/event1"]:
                if Path(candidate).exists():
                    mousedev = candidate
                    break
        if mousedev:
            sdl2.SDL_SetHint(b"SDL_MOUSEDEV", mousedev.encode())
        sdl2.SDL_SetHint(b"SDL_MOUSEDRV", os.environ.get("SDL_MOUSEDRV", "evdev").encode())

        flags = sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_EVENTS | sdl2.SDL_INIT_TIMER
        if sdl2.SDL_Init(flags) < 0:
            logger.error(f"SDL_Init failed: {sdl2.SDL_GetError()}")
            return False

        self.window = sdl2.SDL_CreateWindow(
            b"HueMedia",
            sdl2.SDL_WINDOWPOS_UNDEFINED,
            sdl2.SDL_WINDOWPOS_UNDEFINED,
            WIDTH, HEIGHT,
            sdl2.SDL_WINDOW_FULLSCREEN
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

        if _HAS_TTF and sdlttf:
            if sdlttf.TTF_Init() < 0:
                logger.error(f"TTF_Init failed: {sdlttf.TTF_GetError()}")
            else:
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
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
                    if self.font_12:
                        logger.info(f"Loaded font: {chosen.decode()}")
                    else:
                        logger.warning(f"Failed to open font: {chosen.decode()}")
        else:
            logger.warning("SDL2_ttf not available — text rendering disabled")

        self.running = True
        self.last_tick = sdl2.SDL_GetTicks()
        return True

    def begin_frame(self):
        _safe_render_set_draw_color(self.renderer, BG_DARK)
        _safe_render_clear(self.renderer)
        now = sdl2.SDL_GetTicks()
        dt = now - self.last_tick
        self.last_tick = now
        self.clock += dt
        return dt

    def end_frame(self):
        _safe_render_present(self.renderer)
        elapsed = sdl2.SDL_GetTicks() - self.last_tick
        if elapsed < (1000 // FPS):
            sdl2.SDL_Delay((1000 // FPS) - elapsed)

    def render_rect(self, x, y, w, h, color, radius=0):
        rect = sdl2.SDL_Rect(int(x), int(y), int(w), int(h))
        _safe_render_set_draw_color(self.renderer, color)
        if radius > 0:
            self._rounded_rect(int(x), int(y), int(w), int(h), int(radius))
        else:
            _safe_render_fill_rect(self.renderer, rect)

    def _rounded_rect(self, x, y, w, h, r):
        r = min(r, w // 2, h // 2)
        inner = sdl2.SDL_Rect(x + r, y, w - 2 * r, h)
        _safe_render_fill_rect(self.renderer, inner)
        inner = sdl2.SDL_Rect(x, y + r, w, h - 2 * r)
        _safe_render_fill_rect(self.renderer, inner)
        # Corner quarter-circles using small filled rects (much faster than pixel loops)
        for cx, cy in [(x + r, y + r), (x + w - r - 1, y + r),
                       (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)]:
            self._fill_corner(cx, cy, r)

    def _fill_corner(self, cx, cy, r):
        if r <= 2:
            _safe_render_fill_rect(self.renderer, sdl2.SDL_Rect(cx, cy, 1, 1))
            return
        step = max(1, r // 4)
        for dy in range(0, r, step):
            dx_max = int((r * r - dy * dy) ** 0.5)
            if dx_max > 0:
                col_w = min(step, dx_max)
                if col_w > 0:
                    for sign in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                        px = cx + sign[0] * (dx_max - col_w)
                        py = cy + sign[1] * dy
                        _safe_render_fill_rect(self.renderer, sdl2.SDL_Rect(px, py, col_w, step))

    def render_text(self, text, x, y, color, font=None, center_x=False, center_y=False):
        if font is None:
            font = self.font_14
        if font is None or not text or not _HAS_TTF:
            return 0, 0

        if isinstance(text, str):
            text_bytes = text.encode("utf-8")
        else:
            text_bytes = text

        surf = None
        try:
            surf = sdlttf.TTF_RenderUTF8_Blended(font, text_bytes, color)
        except Exception:
            pass

        if not surf:
            try:
                surf = sdlttf.TTF_RenderText_Blended(font, text_bytes, color)
            except Exception:
                return 0, 0

        if not surf:
            return 0, 0

        tex = sdl2.SDL_CreateTextureFromSurface(self.renderer, surf)
        if not tex:
            sdl2.SDL_FreeSurface(surf)
            return 0, 0

        tw = int(surf.contents.w)
        th = int(surf.contents.h)
        rx, ry = x, y
        if center_x:
            rx = x - tw // 2
        if center_y:
            ry = y - th // 2

        dst = sdl2.SDL_Rect(rx, ry, tw, th)
        _safe_render_copy(self.renderer, tex, None, dst)
        sdl2.SDL_DestroyTexture(tex)
        sdl2.SDL_FreeSurface(surf)
        return tw, th

    def render_texture(self, tex, x, y, w=None, h=None):
        if not tex:
            return
        dst = sdl2.SDL_Rect(int(x), int(y), int(w or 0), int(h or 0))
        _safe_render_copy(self.renderer, tex, None, dst)

    def render_line(self, x1, y1, x2, y2, color, width=1):
        _safe_render_set_draw_color(self.renderer, color)
        for i in range(width):
            _safe_render_draw_line(self.renderer, x1, y1 + i, x2, y2 + i)

    def fill(self, color):
        _safe_render_set_draw_color(self.renderer, color)
        _safe_render_clear(self.renderer)

    def poll_events(self):
        events = []
        ev = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(ev):
            etype = int(ev.type)
            if etype == sdl2.SDL_QUIT:
                self.running = False
            elif etype == sdl2.SDL_FINGERDOWN:
                events.append({
                    "type": "touch",
                    "action": "down",
                    "x": int(ev.tfinger.x * WIDTH),
                    "y": int(ev.tfinger.y * HEIGHT),
                    "finger_id": int(ev.tfinger.fingerId),
                })
            elif etype == sdl2.SDL_FINGERUP:
                events.append({
                    "type": "touch",
                    "action": "up",
                    "x": int(ev.tfinger.x * WIDTH),
                    "y": int(ev.tfinger.y * HEIGHT),
                    "finger_id": int(ev.tfinger.fingerId),
                })
            elif etype == sdl2.SDL_FINGERMOTION:
                events.append({
                    "type": "touch",
                    "action": "move",
                    "x": int(ev.tfinger.x * WIDTH),
                    "y": int(ev.tfinger.y * HEIGHT),
                    "finger_id": int(ev.tfinger.fingerId),
                })
            elif etype == sdl2.SDL_MOUSEBUTTONDOWN:
                events.append({
                    "type": "mouse",
                    "action": "down",
                    "x": int(ev.button.x),
                    "y": int(ev.button.y),
                    "button": int(ev.button.button),
                })
            elif etype == sdl2.SDL_MOUSEBUTTONUP:
                events.append({
                    "type": "mouse",
                    "action": "up",
                    "x": int(ev.button.x),
                    "y": int(ev.button.y),
                    "button": int(ev.button.button),
                })
            elif etype == sdl2.SDL_KEYDOWN:
                events.append({
                    "type": "key",
                    "action": "down",
                    "key": int(ev.key.keysym.sym),
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
        if _HAS_TTF and sdlttf:
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

        if self.current_name is None and self.screens:
            self.switch(list(self.screens.keys())[0])

        while self.disp.running:
            self.disp.begin_frame()

            for ev in self.disp.poll_events():
                if ev["type"] == "key" and ev["key"] == sdl2.SDLK_ESCAPE:
                    self.disp.running = False
                self.handle_event(ev)

            self.render()
            self.disp.end_frame()

            if self.current:
                self.current.tick()

        self.disp.cleanup()
        logger.info("SDL2 UI stopped")
