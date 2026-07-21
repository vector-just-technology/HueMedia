"""Streaming API endpoints — YouTube, Spotify search, play, download."""

import os
import json
import subprocess
from pathlib import Path
from flask import Blueprint, jsonify, request

import main as api_main

stream_bp = Blueprint("stream", __name__)


@stream_bp.route("/search", methods=["POST"])
def search():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    source = data.get("source", "youtube")
    video = data.get("video", False)

    if not query:
        return jsonify({"results": []})

    from player.providers import YouTubeProvider, SpotifyProvider

    if source == "youtube":
        provider = YouTubeProvider()
        results = provider.search(query, video=video)
    elif source == "spotify":
        provider = SpotifyProvider()
        results = provider.search(query)
    else:
        results = []

    return jsonify({"results": results})


@stream_bp.route("/play", methods=["POST"])
def play():
    data = request.get_json() or {}
    url = data.get("url", "")
    source = data.get("source", "youtube")
    video = data.get("video", False)
    title = data.get("title", "Stream")
    artist = data.get("artist", "Unknown")
    cover = data.get("cover", "")

    if not url:
        return jsonify({"error": "no url"}), 400

    eng = api_main.engine
    if not eng:
        return jsonify({"error": "engine unavailable"}), 500

    if source == "youtube":
        from player.providers import YouTubeProvider
        provider = YouTubeProvider()
        stream_url = provider.get_stream_url(url, video=video)
        if not stream_url:
            return jsonify({"error": "failed to get stream"}), 500

        track = {
            "path": stream_url,
            "title": title,
            "artist": artist,
            "album": "Streaming",
            "cover": cover,
            "source": "youtube",
            "is_video": video,
            "stream_url": url,
        }
        eng.play(track)
        return jsonify(eng.get_status())

    elif source == "spotify":
        track = {
            "path": url,
            "title": title,
            "artist": artist,
            "album": "Streaming",
            "cover": cover,
            "source": "spotify",
        }
        eng.play(track)
        return jsonify(eng.get_status())

    return jsonify({"error": "unknown source"}), 400


@stream_bp.route("/stream-url", methods=["POST"])
def stream_url():
    data = request.get_json() or {}
    url = data.get("url", "")
    video = data.get("video", False)

    if not url:
        return jsonify({"error": "no url"}), 400

    from player.providers import YouTubeProvider
    provider = YouTubeProvider()
    stream = provider.get_stream_url(url, video=video)
    info = provider.get_video_info(url)

    return jsonify({
        "stream_url": stream,
        "info": {
            "title": info.get("title", "") if info else "",
            "duration": info.get("duration", 0) if info else 0,
            "thumbnail": info.get("thumbnail", "") if info else "",
        } if info else {},
    })


@stream_bp.route("/download", methods=["POST"])
def download():
    data = request.get_json() or {}
    url = data.get("url", "")
    source = data.get("source", "youtube")
    title = data.get("title", "Unknown")
    artist = data.get("artist", "Unknown")
    cover = data.get("cover", "")
    video = data.get("video", False)

    if not url:
        return jsonify({"error": "no url"}), 400

    import re
    safe_artist = re.sub(r'[^\w\s-]', '', artist).strip() or "Unknown"
    safe_title = re.sub(r'[^\w\s-]', '', title).strip() or "Unknown"
    dest = f"/pool/Music/_Streaming/{safe_artist}/{safe_title}"
    Path(dest).mkdir(parents=True, exist_ok=True)

    result_path = None
    if source == "youtube":
        from player.providers import YouTubeProvider
        provider = YouTubeProvider()
        result_path = provider.download(url, dest, video=video)
    elif source == "spotify":
        from player.providers import SpotifyProvider
        provider = SpotifyProvider()
        result_path = provider.download(url, dest)

    if cover:
        from player.providers import DownloadManager
        DownloadManager.save_cover(cover, Path(dest))

    if result_path:
        api_main.library.scan()
        return jsonify({
            "status": "downloaded",
            "path": result_path,
            "title": safe_title,
            "artist": safe_artist,
        })

    return jsonify({"error": "download failed"}), 500


@stream_bp.route("/downloads")
def list_downloads():
    from player.providers import DownloadManager
    tracks = DownloadManager.get_saved_tracks()
    return jsonify({"tracks": tracks})


@stream_bp.route("/download/<path:track_id>", methods=["DELETE"])
def remove_download(track_id):
    from player.providers import DownloadManager
    ok = DownloadManager.remove_track(track_id)
    if ok:
        api_main.library.scan()
        return jsonify({"status": "removed"})
    return jsonify({"error": "not found"}), 404
