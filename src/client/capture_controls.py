# src/client/capture_controls.py
from __future__ import annotations

from typing import Optional
from src.core.udp_capture import (
    start_capture,
    stop_capture,
    build_bpf_filter,
    UdpCaptureHandle,
)

class UdpCaptureController:
    def __init__(self):
        self._handle: Optional[UdpCaptureHandle] = None

    def start(self, iface: str | None = None, ip: str | None = None, port: int | None = 5056,
              pcap_out: str = "captures/albion_udp.pcap", save_json: bool = True, json_out: str | None = None) -> bool:
        if self._handle is not None:
            return False
        bpf = build_bpf_filter(ip, port)
        self._handle = start_capture(iface=iface, bpf_filter=bpf, pcap_out=pcap_out, save_json=save_json, json_out=json_out)
        return True

    def stop(self) -> bool:
        if self._handle is None:
            return False
        stop_capture(self._handle)
        self._handle = None
        return True

    @property
    def running(self) -> bool:
        return self._handle is not None
