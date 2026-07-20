#!/usr/bin/env python3
"""HueMedia Recovery Server — port 3000

Runs on every boot to check system health after LCD-35-Show driver install.
If everything is OK, triggers the final setup. Otherwise, shows a recovery page.

This server must NOT depend on anything that the LCD driver might break.
Minimal dependencies: flask (no DB, no complex libs).
"""

import os
import sys
import subprocess
import json
import time
import socket
import logging
from pathlib import Path

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='[recovery] %(message)s')

HUE_DIR = "/opt/hue-media"
SETUP_COMPLETE = Path(f"{HUE_DIR}/.setup-complete")
PHASE1_MARKER = Path("/boot/hue-media-phase1")
PHASE1_MARKER2 = Path("/boot/firmware/hue-media-phase1")
SETUP_SCRIPT = f"{HUE_DIR}/setup/02-finalize.sh"


# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
def check_lcd():
    """Check if the LCD framebuffer is active."""
    fb1 = Path("/dev/fb1")
    fb0 = Path("/dev/fb0")

    if fb1.exists():
        try:
            size = fb1.stat().st_size
            if size > 0:
                return {"status": "ok", "device": "/dev/fb1", "size": size}
        except OSError:
            pass

    # Check for any non-HDMI framebuffer
    for fb in Path("/sys/class/graphics").glob("fb*"):
        try:
            name = (fb / "name").read_text().strip()
            if "HDMI" not in name and "main" not in name:
                return {"status": "ok", "device": f"/dev/{fb.name}", "name": name}
        except (OSError, FileNotFoundError):
            pass

    return {"status": "missing", "device": "/dev/fb1", "detail": "LCD framebuffer not detected"}


def check_ssh():
    """Check if SSH is enabled and running."""
    # Check if sshd is running
    result = subprocess.run(
        ["systemctl", "is-active", "ssh"], capture_output=True, text=True
    )
    if result.returncode == 0:
        return {"status": "ok", "service": "ssh", "active": True}

    result = subprocess.run(
        ["systemctl", "is-active", "sshd"], capture_output=True, text=True
    )
    if result.returncode == 0:
        return {"status": "ok", "service": "sshd", "active": True}

    return {"status": "stopped", "detail": "SSH service is not running"}


def check_network():
    """Check network is up with the expected IP."""
    try:
        result = subprocess.run(
            ["ip", "-4", "-o", "addr", "show"], capture_output=True, text=True
        )
        ips = []
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 4:
                ips.append(parts[3].split("/")[0])
        return {"status": "ok", "ips": ips}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def check_writable():
    """Check if music drives are writable (for SAMBA)."""
    for p in ["/pool/Music", "/mnt/music"]:
        if os.path.ismount(p):
            test_file = os.path.join(p, ".hue-write-test")
            try:
                Path(test_file).write_text("ok")
                os.remove(test_file)
                return {"status": "ok", "path": p, "writable": True}
            except OSError:
                return {"status": "error", "path": p, "writable": False}
    return {"status": "missing", "detail": "No music drives mounted"}


def get_all_checks():
    return {
        "lcd": check_lcd(),
        "ssh": check_ssh(),
        "network": check_network(),
        "storage": check_writable(),
    }


# ---------------------------------------------------------------------------
# Recovery Actions
# ---------------------------------------------------------------------------
def enable_ssh():
    """Re-enable SSH service."""
    for svc in ["ssh", "sshd"]:
        subprocess.run(["systemctl", "enable", svc], capture_output=True)
        subprocess.run(["systemctl", "start", svc], capture_output=True)
    # Also ensure ssh file for first-boot
    Path("/boot/ssh").touch(exist_ok=True)
    Path("/boot/firmware/ssh").touch(exist_ok=True)
    return {"status": "ssh_enabled"}


def retry_lcd():
    """Re-attempt LCD driver installation."""
    lcd_scripts = [
        "/opt/lcd-show/LCD35-show",
        "/opt/lcd-show/LCD35-show-v2",
        "/opt/lcd-show/hosyond/LCD35-show",
    ]
    for script in lcd_scripts:
        if Path(script).exists():
            subprocess.Popen(["bash", script])
            return {"status": "retrying", "script": script}

    return {"status": "no_script", "detail": "LCD driver script not found"}


def skip_lcd():
    """Skip LCD and proceed with setup (HDMI mode)."""
    # Create a dummy framebuffer config
    Path("/opt/hue-media/.no-lcd").touch()
    return {"status": "skipped"}


def start_final_setup():
    """Trigger the final system setup."""
    if Path(SETUP_SCRIPT).exists():
        subprocess.Popen(["bash", SETUP_SCRIPT])
        return {"status": "started", "script": SETUP_SCRIPT}
    return {"status": "missing", "detail": "Setup script not found"}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    checks = get_all_checks()
    all_ok = all(v.get("status") == "ok" for v in checks.values())
    setup_done = SETUP_COMPLETE.exists()

    return render_template(
        "recovery.html",
        checks=checks,
        all_ok=all_ok,
        setup_done=setup_done,
        hostname=socket.gethostname(),
    )


@app.route("/api/status")
def api_status():
    return jsonify({
        "checks": get_all_checks(),
        "setup_complete": SETUP_COMPLETE.exists(),
        "phase1": PHASE1_MARKER.exists() or PHASE1_MARKER2.exists(),
    })


@app.route("/api/action/<action>", methods=["POST"])
def api_action(action):
    actions = {
        "enable-ssh": enable_ssh,
        "retry-lcd": retry_lcd,
        "skip-lcd": skip_lcd,
        "start-setup": start_final_setup,
        "check": get_all_checks,
    }

    if action in actions:
        result = actions[action]()
        if action == "check":
            return jsonify(result)
        return jsonify({"action": action, "result": result})
    return jsonify({"error": "unknown action"}), 400


@app.route("/api/logs")
def api_logs():
    try:
        log = Path("/var/log/hue-setup.log")
        if log.exists():
            return log.read_text()
        return "No log file found"
    except Exception as e:
        return str(e)


# ---------------------------------------------------------------------------
# Boot-time logic: auto-proceed if all checks pass
# ---------------------------------------------------------------------------
def auto_heal():
    phase1 = PHASE1_MARKER.exists() or PHASE1_MARKER2.exists()

    if not phase1:
        return  # Phase 1 hasn't been completed yet — just serve the page

    if SETUP_COMPLETE.exists():
        return  # Setup already done

    checks = get_all_checks()
    lcd_ok = checks["lcd"]["status"] == "ok"
    ssh_ok = checks["ssh"]["status"] == "ok"

    if lcd_ok and ssh_ok:
        logging.info("All systems OK — starting final setup")
        start_final_setup()
    elif lcd_ok and not ssh_ok:
        logging.warning("LCD OK but SSH down — enabling SSH")
        enable_ssh()
        time.sleep(2)
        if check_ssh()["status"] == "ok":
            start_final_setup()
    else:
        logging.warning("LCD not ready — waiting for user intervention")


if __name__ == "__main__":
    # Run auto-heal check on startup
    time.sleep(5)
    try:
        auto_heal()
    except Exception as e:
        logging.error(f"Auto-heal failed: {e}")

    app.run(host="0.0.0.0", port=3000, debug=False)
