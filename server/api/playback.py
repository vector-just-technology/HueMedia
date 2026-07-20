"""Playback control API endpoints."""

from flask import Blueprint, jsonify, request
import main as api_main

playback_bp = Blueprint("playback", __name__)


@playback_bp.route("/status")
def status():
    eng = api_main.engine
    if not eng:
        return jsonify({"state": "unavailable"})
    return jsonify(eng.get_status())


@playback_bp.route("/play", methods=["POST"])
def play():
    eng = api_main.engine
    data = request.get_json() or {}
    path = data.get("path")

    if not path:
        return jsonify({"error": "no path"}), 400

    if api_main.library:
        # Look up track by path
        tracks = api_main.library.get_all_tracks()
        for t in tracks:
            if t["path"] == path:
                eng.play(t)
                return jsonify(eng.get_status())

    # Fall back to direct file play
    eng.play_file(path)
    return jsonify(eng.get_status())


@playback_bp.route("/play/<int:track_id>", methods=["POST"])
def play_by_id(track_id):
    eng = api_main.engine
    lib = api_main.library
    if not eng or not lib:
        return jsonify({"error": "unavailable"}), 500

    track = lib.get_track_by_id(track_id)
    if not track:
        return jsonify({"error": "track not found"}), 404

    eng.play(track)
    return jsonify(eng.get_status())


@playback_bp.route("/toggle", methods=["POST"])
def toggle():
    eng = api_main.engine
    if eng:
        eng.toggle_pause()
        return jsonify(eng.get_status())
    return jsonify({"error": "unavailable"}), 500


@playback_bp.route("/stop", methods=["POST"])
def stop():
    eng = api_main.engine
    if eng:
        eng.stop()
        return jsonify(eng.get_status())
    return jsonify({"error": "unavailable"}), 500


@playback_bp.route("/next", methods=["POST"])
def next_track():
    eng = api_main.engine
    if eng:
        eng.next()
        return jsonify(eng.get_status())
    return jsonify({"error": "unavailable"}), 500


@playback_bp.route("/previous", methods=["POST"])
def previous():
    eng = api_main.engine
    if eng:
        eng.previous()
        return jsonify(eng.get_status())
    return jsonify({"error": "unavailable"}), 500


@playback_bp.route("/seek", methods=["POST"])
def seek():
    eng = api_main.engine
    data = request.get_json() or {}
    pos = data.get("position", 0)
    if eng:
        eng.seek(float(pos))
        return jsonify(eng.get_status())
    return jsonify({"error": "unavailable"}), 500


@playback_bp.route("/volume", methods=["GET", "POST"])
def volume():
    eng = api_main.engine
    if not eng:
        return jsonify({"error": "unavailable"}), 500

    if request.method == "POST":
        data = request.get_json() or {}
        vol = data.get("volume", 50)
        eng.set_volume(int(vol))

    return jsonify({"volume": eng.get_status().get("volume", 50)})


@playback_bp.route("/shuffle", methods=["POST"])
def shuffle():
    eng = api_main.engine
    if eng:
        eng.toggle_shuffle()
        return jsonify(eng.get_status())
    return jsonify({"error": "unavailable"}), 500


@playback_bp.route("/repeat", methods=["POST"])
def repeat():
    eng = api_main.engine
    if eng:
        eng.cycle_repeat()
        return jsonify(eng.get_status())
    return jsonify({"error": "unavailable"}), 500


@playback_bp.route("/queue", methods=["GET", "POST"])
def queue():
    eng = api_main.engine
    lib = api_main.library
    if not eng:
        return jsonify({"error": "unavailable"}), 500

    if request.method == "POST":
        data = request.get_json() or {}
        track_ids = data.get("track_ids", [])
        tracks = [lib.get_track_by_id(tid) for tid in track_ids if lib]
        tracks = [t for t in tracks if t]
        eng.set_queue(tracks)

    return jsonify({
        "queue": eng.get_status().get("queue", []),
    })


@playback_bp.route("/queue/clear", methods=["POST"])
def clear_queue():
    eng = api_main.engine
    if eng:
        eng.clear_queue()
        return jsonify({"status": "cleared"})
    return jsonify({"error": "unavailable"}), 500
