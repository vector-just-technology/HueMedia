"""HueMedia configuration"""

import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.path.expanduser("~/.config/hue-media"))
CONFIG_FILE = CONFIG_DIR / "config.json"
LIBRARY_CACHE = CONFIG_DIR / "library.json"

DEFAULT_CONFIG = {
    "volume": 80,
    "shuffle": False,
    "repeat": "off",
    "music_dirs": ["/pool/Music", os.path.expanduser("~/Music")],
    "bluetooth_auto_reconnect": True,
    "theme": "dark",
    "providers": {
        "spotify": {"enabled": False, "username": "", "password": ""},
        "youtube": {"enabled": True, "quality": "bestaudio"},
    },
    "display": {
        "brightness": 100,
        "rotate": 0,
        "timeout_secs": 300,
    },
}

REPEAT_MODES = ["off", "all", "one"]


def ensure_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
    return CONFIG_FILE


def load_config():
    ensure_config()
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    except (json.JSONDecodeError, FileNotFoundError):
        return dict(DEFAULT_CONFIG)


def save_config(cfg):
    ensure_config()
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
