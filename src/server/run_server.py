# src/server/run_server.py
from __future__ import annotations

from flask import Flask, request, jsonify
import os
from typing import Optional

from src.core.udp_capture import (
    start_capture,
    stop_capture,
    build_bpf_filter,
    UdpCaptureHandle,
)

app = Flask(__name__)
capture_handle: Optional[UdpCaptureHandle] = None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "albion-beacon", "capture": capture_handle is not None})


@app.route("/capture/start", methods=["POST"])
def capture_start():
    global capture_handle
    if capture_handle is not None:
        return jsonify({"status": "already_running"}), 400

    data = request.get_json(force=True, silent=True) or {}
    iface = data.get("iface")
    ip = data.get("filter_ip")
    port = data.get("filter_port") or 5056
    pcap_out = data.get("pcap_out", "captures/albion_udp.pcap")
    save_json = bool(data.get("save_json", True))
    json_out = data.get("json_out")

    bpf = build_bpf_filter(ip, port)
    capture_handle = start_capture(
        iface=iface,
        bpf_filter=bpf,
        pcap_out=pcap_out,
        save_json=save_json,
        json_out=json_out,
    )
    return jsonify({"status": "started", "iface": iface, "filter": bpf})


@app.route("/capture/stop", methods=["POST"])
def capture_stop():
    global capture_handle
    if capture_handle is None:
        return jsonify({"status": "not_running"}), 400
    stop_capture(capture_handle)
    capture_handle = None
    return jsonify({"status": "stopped"})


if __name__ == "__main__":
    os.makedirs("captures", exist_ok=True)
    # 개발 중에는 debug=True, 배포 시 False
    app.run(host="0.0.0.0", port=5000, debug=True)
