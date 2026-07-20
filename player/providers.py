"""Streaming providers — Spotify, YouTube, and web radio."""

import logging
import subprocess
import threading
import json
import re
from typing import Optional, Callable
from pathlib import Path

logger = logging.getLogger("providers")


class YouTubeProvider:
    def __init__(self):
        self._search_results = []

    def search(self, query: str) -> list:
        try:
            result = subprocess.run(
                ["yt-dlp", "--flat-playlist", "-J", f"ytsearch10:{query}"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                entries = data.get("entries", [])
                tracks = []
                for i, entry in enumerate(entries):
                    tracks.append({
                        "id": f"yt-{i}",
                        "title": entry.get("title", "Unknown"),
                        "artist": entry.get("channel", "Unknown"),
                        "duration": entry.get("duration", 0),
                        "url": f"https://youtube.com/watch?v={entry.get('id', '')}",
                        "source": "youtube",
                        "cover": entry.get("thumbnail", ""),
                    })
                self._search_results = tracks
                return tracks
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
        return []

    def get_stream_url(self, url: str) -> Optional[str]:
        try:
            result = subprocess.run(
                ["yt-dlp", "-g", "-f", "bestaudio", url],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.error(f"YouTube stream error: {e}")
        return None


class SpotifyProvider:
    def __init__(self):
        self._running = False

    def start(self):
        try:
            subprocess.Popen(
                ["librespot", "--name", "HueMedia", "--bitrate", "320",
                 "--enable-volume-normalisation", "--initial-volume", "80",
                 "--backend", "pipe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._running = True
            logger.info("Spotify (librespot) started")
        except FileNotFoundError:
            logger.warning("librespot not installed")

    def stop(self):
        subprocess.run(["pkill", "librespot"], capture_output=True)
        self._running = False

    def search(self, query: str) -> list:
        try:
            result = subprocess.run(
                ["librespot", "--search", query, "--json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Spotify search error: {e}")
        return []


class RadioBrowserProvider:
    def __init__(self):
        self._api = "https://de1.api.radio-browser.info"

    def search(self, query: str) -> list:
        import requests
        try:
            r = requests.post(
                f"{self._api}/json/stations/search",
                json={"name": query, "limit": 20},
                timeout=10,
            )
            if r.status_code == 200:
                stations = r.json()
                return [{
                    "id": f"radio-{s.get('stationuuid', '')}",
                    "title": s.get("name", "Unknown"),
                    "artist": s.get("country", ""),
                    "url": s.get("url", ""),
                    "source": "radio",
                    "cover": s.get("favicon", ""),
                } for s in stations]
        except Exception as e:
            logger.error(f"Radio search error: {e}")
        return []
