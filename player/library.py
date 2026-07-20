"""Music library scanner — discovers tracks from configured directories."""

import json
import os
import threading
from pathlib import Path
from typing import List, Optional

from config import load_config, LIBRARY_CACHE

AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a", ".wma", ".opus"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".ts", ".mts", ".m2ts"}
COVER_NAMES = {"cover.png", "cover.jpg", "folder.jpg", "album.png", "album.jpg", "front.png"}


class MusicLibrary:
    def __init__(self):
        self._artists = {}
        self._tracks = []
        self._scanning = False
        self._lock = threading.Lock()
        self._listeners = []

    def add_listener(self, cb):
        self._listeners.append(cb)

    def _notify(self):
        for cb in self._listeners:
            try:
                cb(self._artists)
            except Exception:
                pass

    def scan(self):
        if self._scanning:
            return
        self._scanning = True

        def _scan():
            cfg = load_config()
            dirs = cfg.get("music_dirs", ["/pool/Music", os.path.expanduser("~/Music")])
            new_artists = {}
            new_tracks = []
            idx = 0

            for music_dir in dirs:
                base = Path(music_dir)
                if not base.exists():
                    continue

                for entry in base.iterdir():
                    if not entry.is_dir():
                        continue
                    artist_name = entry.name
                    if artist_name.startswith("."):
                        continue

                    songs = []
                    for song_dir in entry.iterdir():
                        if not song_dir.is_dir():
                            continue
                        if song_dir.name.startswith("."):
                            continue
                        cover = self._find_cover(song_dir)
                        mp3_files = sorted(
                            [f for f in song_dir.iterdir()
                             if f.suffix.lower() in AUDIO_EXTENSIONS]
                        )
                        for mp3 in mp3_files:
                            track = {
                                "id": idx,
                                "path": str(mp3),
                                "title": mp3.stem,
                                "artist": artist_name,
                                "album": song_dir.name,
                                "cover": cover,
                                "duration": 0.0,
                            }
                            songs.append(track)
                            new_tracks.append(track)
                            idx += 1

                        video_files = sorted(
                            [f for f in song_dir.iterdir()
                             if f.suffix.lower() in VIDEO_EXTENSIONS]
                        )
                        for vid in video_files:
                            track = {
                                "id": idx,
                                "path": str(vid),
                                "title": vid.stem,
                                "artist": artist_name,
                                "album": song_dir.name,
                                "cover": cover or self._find_cover(song_dir),
                                "duration": 0.0,
                                "is_video": True,
                            }
                            songs.append(track)
                            new_tracks.append(track)
                            idx += 1

                    if songs:
                        new_artists[artist_name] = {
                            "name": artist_name,
                            "songs": songs,
                            "count": len(songs),
                        }

            with self._lock:
                self._artists = dict(sorted(new_artists.items()))
                self._tracks = new_tracks
            self._cache()
            self._scanning = False
            self._notify()

        threading.Thread(target=_scan, daemon=True).start()

    def get_artists(self) -> List[dict]:
        with self._lock:
            return list(self._artists.values())

    def get_artist(self, name: str) -> Optional[dict]:
        with self._lock:
            return self._artists.get(name)

    def get_all_tracks(self) -> List[dict]:
        with self._lock:
            return list(self._tracks)

    def get_track_by_id(self, tid: int) -> Optional[dict]:
        with self._lock:
            for t in self._tracks:
                if t["id"] == tid:
                    return t
            return None

    def search(self, query: str) -> List[dict]:
        q = query.lower()
        results = []
        with self._lock:
            for t in self._tracks:
                if q in t["title"].lower() or q in t["artist"].lower() or q in t["album"].lower():
                    results.append(t)
        return results

    @staticmethod
    def _find_cover(dir_path: Path) -> Optional[str]:
        for name in COVER_NAMES:
            f = dir_path / name
            if f.exists():
                return str(f)
        return None

    def _cache(self):
        try:
            with self._lock:
                data = {
                    "artists": {k: {
                        "name": v["name"],
                        "count": v["count"],
                        "songs": [{
                            "id": s["id"],
                            "path": s["path"],
                            "title": s["title"],
                            "artist": s["artist"],
                            "album": s["album"],
                            "cover": s["cover"],
                        } for s in v["songs"]]
                    } for k, v in self._artists.items()}
                }
            with open(LIBRARY_CACHE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def load_cache(self) -> bool:
        if LIBRARY_CACHE.exists():
            try:
                with open(LIBRARY_CACHE) as f:
                    data = json.load(f)
                artists = data.get("artists", {})
                tracks = []
                for artist_data in artists.values():
                    for s in artist_data.get("songs", []):
                        tracks.append(s)
                with self._lock:
                    self._artists = artists
                    self._tracks = tracks
                return True
            except Exception:
                return False
        return False
