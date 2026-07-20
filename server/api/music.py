"""Music library API endpoints."""

import os
import json
from pathlib import Path
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

music_bp = Blueprint("music", __name__)

# These are set at import time by run.py
import sys
import main as api_main


@music_bp.route("/artists")
def list_artists():
    lib = api_main.library
    if not lib:
        return jsonify([])
    artists = lib.get_artists()
    return jsonify([{
        "name": a["name"],
        "count": a["count"],
    } for a in artists])


@music_bp.route("/artists/<artist_name>")
def get_artist(artist_name):
    lib = api_main.library
    if not lib:
        return jsonify({"error": "no library"}), 500
    artist = lib.get_artist(artist_name)
    if not artist:
        return jsonify({"error": "not found"}), 404
    return jsonify(artist)


@music_bp.route("/tracks")
def list_tracks():
    lib = api_main.library
    if not lib:
        return jsonify([])
    artist = request.args.get("artist")
    album = request.args.get("album")
    q = request.args.get("q")

    if q:
        tracks = lib.search(q)
    elif artist:
        a = lib.get_artist(artist)
        tracks = a["songs"] if a else []
    else:
        tracks = lib.get_all_tracks()

    return jsonify(tracks)


@music_bp.route("/search")
def search():
    q = request.args.get("q", "")
    lib = api_main.library
    if not lib or not q:
        return jsonify([])
    return jsonify(lib.search(q))


@music_bp.route("/cover")
def get_cover():
    path = request.args.get("path", "")
    if path and Path(path).exists():
        from flask import send_file
        return send_file(path, mimetype="image/png")
    return jsonify({"error": "not found"}), 404


@music_bp.route("/rescan", methods=["POST"])
def rescan():
    lib = api_main.library
    if lib:
        lib.scan()
        return jsonify({"status": "scanning"})
    return jsonify({"error": "no library"}), 500


@music_bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    artist = request.form.get("artist", "Unknown")
    album = request.form.get("album", "Unknown")

    music_dir = "/pool/Music"
    target = Path(music_dir) / artist / album
    target.mkdir(parents=True, exist_ok=True)

    filename = secure_filename(file.filename)
    filepath = target / filename
    file.save(str(filepath))

    # If cover image
    if filename.lower().startswith("cover"):
        ext = Path(filename).suffix
        if ext.lower() in {".png", ".jpg", ".jpeg"}:
            # Rename to cover.png
            dest = target / f"cover{ext}"
            if dest.exists():
                dest.unlink()
            filepath.rename(dest)

    return jsonify({"status": "uploaded", "path": str(filepath)})
