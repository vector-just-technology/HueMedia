"""Playback engine — MPV wrapper"""

import os
import time
import threading
import logging
from pathlib import Path
from typing import Optional, Callable

from config import load_config, save_config

logger = logging.getLogger("engine")


class PlaybackEngine:
    def __init__(self):
        self._mpv = None
        self._position = 0.0
        self._duration = 0.0
        self._state = "stopped"
        self._current_track = None
        self._listeners = []
        self._volume = 80
        self._shuffle = False
        self._repeat = "off"
        self._queue = []
        self._history = []
        self._init_mpv()

    def _init_mpv(self):
        try:
            import mpv
            self._mpv = mpv.MPV(
                input_default_bindings=True,
                input_vo_keyboard=True,
                osc=True,
                vid=False,
                vo="null",
                audio_device="auto",
                cache=2048,
                demuxer_max_bytes="10M",
            )

            self._mpv.observe_property("time-pos", self._on_property_change)
            self._mpv.observe_property("duration", self._on_property_change)
            self._mpv.observe_property("pause", self._on_property_change)
            self._mpv.observe_property("eof-reached", self._on_eof)

            cfg = load_config()
            self._volume = cfg.get("volume", 80)
            self._shuffle = cfg.get("shuffle", False)
            self._repeat = cfg.get("repeat", "off")
            self._mpv.volume = self._volume

            self._mpv.loop = "no"
            self._state = "stopped"

        except Exception as e:
            logger.error(f"Failed to initialize MPV: {e}")
            self._state = "error"

    def _mpv_ok(self):
        return self._mpv is not None

    def _on_property_change(self, name, value):
        if name == "time-pos" and value is not None:
            self._position = float(value)
        elif name == "duration" and value is not None:
            self._duration = float(value)
        elif name == "pause":
            self._state = "paused" if value else "playing"
        self._notify()

    def _on_eof(self, name, value):
        if value:
            self._next()

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
            "state": self._state,
            "position": self._position,
            "duration": self._duration,
            "volume": self._volume,
            "shuffle": self._shuffle,
            "repeat": self._repeat,
            "current": self._current_track,
            "queue": [t.get("path", "") for t in self._queue] if self._queue else [],
        }

    def play(self, track: dict):
        if not self._mpv_ok():
            logger.warning("MPV not available")
            return
        path = track.get("path")
        if not path or not Path(path).exists():
            logger.error(f"Track not found: {path}")
            return
        self._current_track = track
        self._mpv.play(path)
        self._state = "loading"
        self._notify()

    def play_file(self, filepath: str):
        if not self._mpv_ok():
            return
        path = Path(filepath)
        if not path.exists():
            return
        track = {
            "path": str(path),
            "title": path.stem,
            "artist": path.parent.parent.name if path.parent.parent else "Unknown",
            "album": path.parent.name if path.parent else "Unknown",
            "cover": self._find_cover(path),
        }
        self.play(track)

    def toggle_pause(self):
        if not self._mpv_ok():
            return
        if self._state == "playing":
            self._mpv.pause = True
        elif self._state == "paused":
            self._mpv.pause = False

    def stop(self):
        if not self._mpv_ok():
            return
        self._mpv.stop()
        self._state = "stopped"
        self._position = 0.0
        self._duration = 0.0
        self._notify()

    def seek(self, position: float):
        if not self._mpv_ok():
            return
        self._mpv.seek(position, "absolute")

    def seek_relative(self, delta: float):
        if not self._mpv_ok():
            return
        self._mpv.seek(delta, "relative")

    def set_volume(self, vol: int):
        self._volume = max(0, min(100, vol))
        if self._mpv_ok():
            self._mpv.volume = self._volume
        cfg = load_config()
        cfg["volume"] = self._volume
        save_config(cfg)
        self._notify()

    def volume_up(self, delta=5):
        self.set_volume(self._volume + delta)

    def volume_down(self, delta=5):
        self.set_volume(self._volume - delta)

    def next(self):
        self._next()

    def previous(self):
        if self._history:
            prev = self._history.pop()
            self._queue.insert(0, prev)
            self._next()

    def _next(self):
        if self._repeat == "one" and self._current_track:
            self.play(self._current_track)
            return

        if self._history:
            self._history.append(self._current_track)
        else:
            self._history = [self._current_track]

        if self._queue:
            next_track = self._queue.pop(0)
            self.play(next_track)
        elif self._repeat == "all" and self._history:
            self._queue = list(self._history)
            self._history = []
            self._next()
        else:
            self.stop()

    def set_queue(self, tracks: list):
        self._queue = list(tracks)
        self._history = []

    def add_to_queue(self, track: dict):
        self._queue.append(track)

    def clear_queue(self):
        self._queue = []
        self._history = []

    def toggle_shuffle(self):
        self._shuffle = not self._shuffle
        cfg = load_config()
        cfg["shuffle"] = self._shuffle
        save_config(cfg)
        self._notify()

    def cycle_repeat(self):
        modes = ["off", "all", "one"]
        idx = modes.index(self._repeat) if self._repeat in modes else 0
        self._repeat = modes[(idx + 1) % len(modes)]
        cfg = load_config()
        cfg["repeat"] = self._repeat
        save_config(cfg)
        self._notify()

    @staticmethod
    def _find_cover(path: Path) -> Optional[str]:
        cover = path.parent / "cover.png"
        if cover.exists():
            return str(cover)
        cover = path.parent / "cover.jpg"
        if cover.exists():
            return str(cover)
        cover = path.parent / "folder.jpg"
        if cover.exists():
            return str(cover)
        return None

    def cleanup(self):
        if self._mpv:
            try:
                self._mpv.terminate()
            except Exception:
                pass
