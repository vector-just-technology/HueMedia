"""HueMedia API Server — Flask application factory."""

import os
import json
import logging
from pathlib import Path
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format="[api] %(levelname)s: %(message)s")
logger = logging.getLogger("api")

# Global references (set by run.py after init)
engine = None
library = None
bt_manager = None
player_dir = None


def create_app():
    app = Flask(__name__, static_folder=None)
    CORS(app)

    # Register blueprints
    from api.music import music_bp
    from api.bluetooth import bt_bp
    from api.system import system_bp
    from api.playback import playback_bp

    app.register_blueprint(music_bp, url_prefix="/api/music")
    app.register_blueprint(bt_bp, url_prefix="/api/bluetooth")
    app.register_blueprint(system_bp, url_prefix="/api/system")
    app.register_blueprint(playback_bp, url_prefix="/api/playback")

    # Serve web UI (built React app or static fallback)
    @app.route("/")
    def index():
        web_dir = os.path.join(player_dir, "web", "dist") if player_dir else None
        if web_dir and os.path.exists(os.path.join(web_dir, "index.html")):
            return send_from_directory(web_dir, "index.html")
        return jsonify({
            "name": "HueMedia",
            "version": "1.0",
            "status": "running",
            "web_ui": "Build web UI with: cd web && npm run build",
        })

    @app.route("/<path:path>")
    def static_files(path):
        web_dir = os.path.join(player_dir, "web", "dist") if player_dir else None
        if web_dir:
            filepath = os.path.join(web_dir, path)
            if os.path.exists(filepath):
                return send_from_directory(web_dir, path)
        return jsonify({"error": "not found"}), 404

    @app.route("/api/status")
    def status():
        return jsonify({
            "status": "ok",
            "playing": engine.get_status() if engine else {},
            "library": {
                "artists": len(library.get_artists()) if library else 0,
                "tracks": len(library.get_all_tracks()) if library else 0,
            } if library else {},
        })

    return app
