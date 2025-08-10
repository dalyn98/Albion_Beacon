# src/core/udp_capture.py
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import threading
from datetime import datetime
from typing import Optional

try:
    # Scapy는 Npcap/WinPcap이 설치된 Windows에서 UDP 캡처 가능
    from scapy.all import sniff, PcapWriter, IP, UDP  # type: ignore
    SCAPY_OK = True
except Exception:
    SCAPY_OK = False


ALBION_DEFAULT_PORT = 5056  # 관측 기반 기본값, 환경에 따라 달라질 수 있음


def _npcap_installed_hint() -> str:
    return (
        "Npcap이 설치되어 있어야 합니다.\n"
        " - 관리자 권한 PowerShell로 실행 권장\n"
        " - 설치 후 재부팅 필요할 수 있음"
    )


def _fail(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def build_bpf_filter(ip: Optional[str], port: Optional[int]) -> str:
    clauses = ["udp"]
    if ip:
        clauses.append(f"host {ip}")
    if port:
        clauses.append(f"port {port}")
    return " and ".join(clauses)


def packet_to_dict(pkt) -> dict:
    ip = pkt.getlayer(IP)
    udp = pkt.getlayer(UDP)
    return {
        "ts": datetime.utcfromtimestamp(float(pkt.time)).isoformat() + "Z",
        "src": f"{ip.src}:{udp.sport}" if ip and udp else None,
        "dst": f"{ip.dst}:{udp.dport}" if ip and udp else None,
        "len": len(pkt),
        "summary": pkt.summary(),
    }


class UdpCaptureHandle:
    """캡처 스레드 제어 핸들"""
    def __init__(self, stop_event: threading.Event, thread: threading.Thread):
        self.stop_event = stop_event
        self.thread = thread

    def stop(self, join_timeout: float = 3.0) -> None:
        self.stop_event.set()
        self.thread.join(join_timeout)


def _ensure_outputs(pcap_out: str, json_out: Optional[str], save_json: bool):
    os.makedirs(os.path.dirname(pcap_out) or ".", exist_ok=True)
    json_path = None
    if save_json:
        json_path = json_out or (os.path.splitext(pcap_out)[0] + ".jsonl")
        os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
    return json_path


def start_capture(
    iface: Optional[str],
    bpf_filter: str,
    pcap_out: str = "captures/albion_udp.pcap",
    save_json: bool = False,
    json_out: Optional[str] = None,
) -> UdpCaptureHandle:
    """
    비차단 캡처 시작. stop_event로 중단.
    - 반환: UdpCaptureHandle (handle.stop() 또는 stop_capture(handle)로 종료)
    """
    if not SCAPY_OK:
        _fail("scapy를 불러오지 못했습니다. Python 환경과 의존성을 확인하세요.\n" + _npcap_installed_hint())

    json_path = _ensure_outputs(pcap_out, json_out, save_json)
    pcap_writer = PcapWriter(pcap_out, append=True, sync=True)
    json_fp = open(json_path, "a", encoding="utf-8") if save_json else None

    stop_event = threading.Event()

    def _on_packet(pkt):
        if stop_event.is_set():
            return
        pcap_writer.write(pkt)
        if json_fp:
            json_fp.write(json.dumps(packet_to_dict(pkt), ensure_ascii=False) + "\n")

    def _run():
        print(f"[INFO] Start capture | iface={iface or 'auto'} | filter='{bpf_filter}'")
        print(f"[INFO] Writing PCAP -> {pcap_out}")
        if json_fp:
            print(f"[INFO] Writing JSONL -> {json_fp.name}")
        try:
            sniff(
                iface=iface,           # None이면 Scapy가 적절히 선택
                filter=bpf_filter,
                prn=_on_packet,
                store=False,
                stop_filter=lambda p: stop_event.is_set(),
            )
        except PermissionError:
            print("[ERROR] 패킷 캡처 권한이 없습니다. 관리자 권한으로 다시 실행하세요.")
            print(_npcap_installed_hint())
        except OSError as e:
            print(f"[ERROR] 인터페이스/드라이버 오류: {e}")
            print(_npcap_installed_hint())
        finally:
            try:
                if json_fp:
                    json_fp.flush()
                    json_fp.close()
                pcap_writer.close()
            except Exception:
                pass
            print("[INFO] Capture thread finished.")

    th = threading.Thread(target=_run, name="albion-udp-capture", daemon=True)
    th.start()
    return UdpCaptureHandle(stop_event=stop_event, thread=th)


def stop_capture(handle: UdpCaptureHandle, join_timeout: float = 3.0) -> None:
    handle.stop(join_timeout=join_timeout)


def cli_main():
    parser = argparse.ArgumentParser(description="Albion Beacon - UDP Packet Capture (Unified)")
    parser.add_argument("--iface", help="캡처할 인터페이스 이름(미지정 시 자동)")
    parser.add_argument("--filter-ip", help="BPF 필터: host <IP>")
    parser.add_argument("--filter-port", type=int, default=ALBION_DEFAULT_PORT, help="BPF 필터: port <PORT>")
    parser.add_argument("--pcap-out", default="captures/albion_udp.pcap", help="PCAP 출력 경로")
    parser.add_argument("--save-json", action="store_true", help="JSONL 병렬 저장")
    parser.add_argument("--json-out", help="JSONL 출력 경로(미지정 시 pcap 경로 기반)")
    parser.add_argument("--duration", type=int, help="캡처 지속 시간(초), 미지정 시 수동 종료")
    args = parser.parse_args()

    bpf = build_bpf_filter(args.filter_ip, args.filter_port)
    handle = start_capture(
        iface=args.iface,
        bpf_filter=bpf,
        pcap_out=args.pcap_out,
        save_json=args.save_json,
        json_out=args.json_out,
    )

    try:
        if args.duration and args.duration > 0:
            time.sleep(args.duration)
        else:
            print("[INFO] Press Ctrl+C to stop capture...")
            while True:
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping capture...")
    finally:
        stop_capture(handle)


if __name__ == "__main__":
    cli_main()
