"""System management API endpoints."""

import os
import subprocess
import json
import platform
from pathlib import Path
from flask import Blueprint, jsonify, request

import main as api_main
from config import Config

system_bp = Blueprint("system", __name__)


@system_bp.route("/info")
def info():
    return jsonify({
        "hostname": platform.node(),
        "platform": platform.platform(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "api_version": "1.0",
        "name": "HueMedia",
    })


@system_bp.route("/resources")
def resources():
    import psutil
    return jsonify({
        "cpu": psutil.cpu_percent(interval=0.5),
        "memory": psutil.virtual_memory()._asdict(),
        "disk": psutil.disk_usage("/")._asdict(),
        "temperature": _get_temp(),
    })


@system_bp.route("/storage")
def storage():
    drives = []
    music_base = Path("/mnt/music")
    if music_base.exists():
        for d in music_base.iterdir():
            if d.is_dir():
                try:
                    usage = os.statvfs(str(d))
                    total = usage.f_frsize * usage.f_blocks
                    free = usage.f_frsize * usage.f_bfree
                    drives.append({
                        "name": d.name,
                        "path": str(d),
                        "total": total,
                        "free": free,
                        "mounted": os.path.ismount(d),
                    })
                except Exception:
                    drives.append({"name": d.name, "path": str(d), "error": True})

    pool = Path("/pool/Music")
    pool_info = {}
    if pool.exists():
        try:
            usage = os.statvfs(str(pool))
            pool_info = {
                "total": usage.f_frsize * usage.f_blocks,
                "free": usage.f_frsize * usage.f_bfree,
                "mounted": os.path.ismount(str(pool)),
            }
        except Exception:
            pass

    return jsonify({"drives": drives, "pool": pool_info})


@system_bp.route("/reboot", methods=["POST"])
def reboot():
    subprocess.Popen(["reboot"])
    return jsonify({"status": "rebooting"})


@system_bp.route("/shutdown", methods=["POST"])
def shutdown():
    subprocess.Popen(["poweroff"])
    return jsonify({"status": "shutting_down"})


@system_bp.route("/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        data = request.get_json() or {}
        try:
            config_path = Path(os.path.expanduser("~/.config/hue-media/config.json"))
            if config_path.exists():
                cfg = json.loads(config_path.read_text())
                cfg.update(data)
                config_path.write_text(json.dumps(cfg, indent=2))
                return jsonify({"status": "saved"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    config_path = Path(os.path.expanduser("~/.config/hue-media/config.json"))
    if config_path.exists():
        return jsonify(json.loads(config_path.read_text()))
    return jsonify({})


@system_bp.route("/shell", methods=["POST"])
def shell():
    data = request.get_json() or {}
    cmd = data.get("cmd", "")

    if not cmd or cmd.strip() == "":
        return jsonify({"output": ""})

    dangerous = ["rm -rf /", "mkfs", "dd if=", "> /dev/sd"]
    for d in dangerous:
        if d in cmd:
            return jsonify({"output": "Command blocked for safety", "error": True})

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return jsonify({
            "output": result.stdout + result.stderr,
            "code": result.returncode,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"output": "Command timed out", "error": True})
    except Exception as e:
        return jsonify({"output": str(e), "error": True})


@system_bp.route("/plugins")
def list_plugins():
    plugins_dir = Path("/opt/hue-media/plugins")
    plugins_dir.mkdir(exist_ok=True)
    plugins = []
    for p in plugins_dir.iterdir():
        if p.suffix == ".py":
            plugins.append({"name": p.stem, "path": str(p)})
    return jsonify(plugins)


@system_bp.route("/logs/<service>")
def logs(service):
    allowed = {"hue-api", "hue-bluetooth"}
    if service not in allowed:
        return jsonify({"error": "invalid service"}), 400

    try:
        result = subprocess.run(
            ["journalctl", "-u", f"{service}.service", "--no-pager", "-n", "100"],
            capture_output=True, text=True, timeout=10
        )
        return jsonify({"logs": result.stdout, "service": service})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _get_temp():
    try:
        temp = Path("/sys/class/thermal/thermal_zone0/temp")
        if temp.exists():
            return round(int(temp.read_text().strip()) / 1000, 1)
    except Exception:
        pass
    return None
