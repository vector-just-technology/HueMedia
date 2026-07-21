"""Streaming providers — YouTube, Spotify, web radio, and download support."""

import logging
import subprocess
import threading
import json
import re
import os
import time
from typing import Optional, Callable
from pathlib import Path

logger = logging.getLogger("providers")

AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a", ".wma", ".opus"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm"}


class YouTubeProvider:
    def __init__(self):
        self._search_results = []

    def search(self, query: str, video: bool = False) -> list:
        try:
            search_type = "ytsearch10" if not video else "ytsearch10"
            result = subprocess.run(
                ["yt-dlp", "--flat-playlist", "-J", f"{search_type}:{query}"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                entries = data.get("entries", [])
                tracks = []
                for i, entry in enumerate(entries):
                    vid = entry.get("id", "")
                    tracks.append({
                        "id": f"yt-{vid}",
                        "title": entry.get("title", "Unknown"),
                        "artist": entry.get("channel", "Unknown"),
                        "channel": entry.get("channel", "Unknown"),
                        "duration": entry.get("duration", 0),
                        "url": f"https://youtube.com/watch?v={vid}",
                        "source": "youtube",
                        "youtube_id": vid,
                        "cover": entry.get("thumbnail", f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"),
                        "is_video": entry.get("is_live", False) or entry.get("duration", 0) > 600,
                    })
                self._search_results = tracks
                return tracks
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
        return []

    def get_stream_url(self, url: str, video: bool = False) -> Optional[str]:
        try:
            fmt = "bestvideo+bestaudio/best" if video else "bestaudio"
            result = subprocess.run(
                ["yt-dlp", "-g", "-f", fmt, url],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0]
        except Exception as e:
            logger.error(f"YouTube stream error: {e}")
        return None

    def download(self, url: str, dest: str, video: bool = False) -> Optional[str]:
        try:
            Path(dest).mkdir(parents=True, exist_ok=True)
            fmt = "bestvideo+bestaudio/best" if video else "bestaudio/best"
            result = subprocess.run(
                ["yt-dlp", "-f", fmt, "-o", f"{dest}/%(title)s.%(ext)s", url],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                for f in Path(dest).iterdir():
                    if f.suffix.lower() in AUDIO_EXTENSIONS | VIDEO_EXTENSIONS:
                        return str(f)
            return None
        except Exception as e:
            logger.error(f"YouTube download error: {e}")
            return None

    def get_video_info(self, url: str) -> Optional[dict]:
        try:
            result = subprocess.run(
                ["yt-dlp", "-J", url],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"YouTube info error: {e}")
        return None


class SpotifyProvider:
    def __init__(self):
        self._running = False

    def search(self, query: str) -> list:
        try:
            result = subprocess.run(
                ["librespot", "--search", query, "--json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                tracks = []
                entries = data.get("tracks", {}).get("items", []) if isinstance(data, dict) else []
                for i, entry in enumerate(entries):
                    track_id = entry.get("id", "") or entry.get("uri", "")
                    tracks.append({
                        "id": f"sp-{track_id}",
                        "title": entry.get("name", "Unknown"),
                        "artist": ", ".join(a.get("name", "") for a in entry.get("artists", [])),
                        "album": entry.get("album", {}).get("name", ""),
                        "duration": entry.get("duration_ms", 0) // 1000,
                        "url": entry.get("uri", "") or entry.get("external_urls", {}).get("spotify", ""),
                        "source": "spotify",
                        "cover": entry.get("album", {}).get("images", [{}])[0].get("url", "") if entry.get("album") else "",
                    })
                return tracks
        except Exception as e:
            logger.error(f"Spotify search error: {e}")
        return []

    def download(self, url: str, dest: str) -> Optional[str]:
        try:
            Path(dest).mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                ["spotdl", "download", url, "--output", f"{dest}/", "--format", "mp3"],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                for f in Path(dest).iterdir():
                    if f.suffix.lower() in AUDIO_EXTENSIONS:
                        return str(f)
            return None
        except Exception as e:
            logger.error(f"Spotify download error: {e}")
            return None


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


class DownloadManager:
    SAVE_DIR = "/pool/Music/_Streaming"

    @classmethod
    def get_saved_tracks(cls) -> list:
        base = Path(cls.SAVE_DIR)
        if not base.exists():
            return []
        tracks = []
        for artist_dir in base.iterdir():
            if not artist_dir.is_dir():
                continue
            for song_dir in artist_dir.iterdir():
                if not song_dir.is_dir():
                    continue
                cover = None
                audio_file = None
                for f in song_dir.iterdir():
                    if f.suffix.lower() in AUDIO_EXTENSIONS | VIDEO_EXTENSIONS:
                        audio_file = str(f)
                    if f.name.lower() in ("cover.png", "cover.jpg", "folder.jpg"):
                        cover = str(f)
                if audio_file:
                    tracks.append({
                        "id": f"saved-{artist_dir.name}-{song_dir.name}",
                        "title": song_dir.name,
                        "artist": artist_dir.name,
                        "path": audio_file,
                        "cover": cover,
                        "source": "saved",
                        "duration": 0,
                    })
        return tracks

    @classmethod
    def save_cover(cls, url: str, dest_dir: Path):
        if not url:
            return
        try:
            import requests
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                ext = ".png" if "png" in r.headers.get("content-type", "") else ".jpg"
                (dest_dir / f"cover{ext}").write_bytes(r.content)
        except Exception as e:
            logger.error(f"Cover download error: {e}")

    @classmethod
    def remove_track(cls, track_id: str) -> bool:
        parts = track_id.split("-", 1)
        if len(parts) < 2:
            return False
        name = parts[1]
        base = Path(cls.SAVE_DIR)
        for artist_dir in base.iterdir():
            if not artist_dir.is_dir():
                continue
            for song_dir in artist_dir.iterdir():
                key = f"saved-{artist_dir.name}-{song_dir.name}"
                if key == track_id:
                    import shutil
                    shutil.rmtree(song_dir)
                    return True
        return False
