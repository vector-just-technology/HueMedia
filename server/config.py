"""API server configuration"""

import os

class Config:
    SECRET_KEY = os.environ.get("HUE_SECRET", "hue-media-default-key")
    DEBUG = False
    HOST = "0.0.0.0"
    PORT = 5000
    MUSIC_DIRS = ["/pool/Music", os.path.expanduser("~/Music")]
    CACHE_DIR = os.path.expanduser("~/.cache/hue-media")
