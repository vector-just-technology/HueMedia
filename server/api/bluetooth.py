"""Bluetooth management API endpoints."""

from flask import Blueprint, jsonify, request
import main as api_main

bt_bp = Blueprint("bluetooth", __name__)


def get_bt():
    return api_main.bt_manager


@bt_bp.route("/status")
def status():
    bt = get_bt()
    if not bt:
        return jsonify({"available": [], "connected": None, "scanning": False})
    return jsonify(bt.get_status())


@bt_bp.route("/scan", methods=["POST"])
def scan():
    bt = get_bt()
    if not bt:
        return jsonify({"error": "bluetooth unavailable"}), 500

    data = request.get_json() or {}
    if data.get("stop"):
        bt.stop_scan()
    else:
        bt.start_scan()

    return jsonify(bt.get_status())


@bt_bp.route("/pair", methods=["POST"])
def pair():
    bt = get_bt()
    if not bt:
        return jsonify({"error": "bluetooth unavailable"}), 500

    data = request.get_json() or {}
    mac = data.get("mac", "")
    if not mac:
        return jsonify({"error": "no mac"}), 400

    bt.pair(mac)
    return jsonify({"status": "pairing", "mac": mac})


@bt_bp.route("/connect", methods=["POST"])
def connect():
    bt = get_bt()
    if not bt:
        return jsonify({"error": "bluetooth unavailable"}), 500

    data = request.get_json() or {}
    mac = data.get("mac", "")
    if not mac:
        return jsonify({"error": "no mac"}), 400

    bt.connect(mac)
    return jsonify({"status": "connecting", "mac": mac})


@bt_bp.route("/disconnect", methods=["POST"])
def disconnect():
    bt = get_bt()
    if not bt:
        return jsonify({"error": "bluetooth unavailable"}), 500

    bt.disconnect()
    return jsonify({"status": "disconnected"})


@bt_bp.route("/forget", methods=["POST"])
def forget():
    bt = get_bt()
    if not bt:
        return jsonify({"error": "bluetooth unavailable"}), 500

    data = request.get_json() or {}
    mac = data.get("mac", "")
    if not mac:
        return jsonify({"error": "no mac"}), 400

    bt.forget(mac)
    return jsonify({"status": "removed", "mac": mac})
