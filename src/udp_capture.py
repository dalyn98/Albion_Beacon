# src/core/udp_capture.py
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

try:
    # Scapy는 Npcap/WinPcap이 설치된 Windows에서 UDP 캡처 가능
    from scapy.all import sniff, PcapWriter, IP, UDP  # type: ignore
    SCAPY_OK = True
except Exception:
    SCAPY_OK = False


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


def capture_udp(
    iface: Optional[str],
    bpf_filter: str,
    pcap_out: str,
    save_json: bool,
    json_out: Optional[str],
    max_packets: Optional[int],
    timeout: Optional[int],
) -> None:
    if not SCAPY_OK:
        _fail("scapy를 불러오지 못했습니다. Python 환경과 의존성을 확인하세요.\n" + _npcap_installed_hint())

    # 출력 준비
    os.makedirs(os.path.dirname(pcap_out) or ".", exist_ok=True)
    pcap_writer = PcapWriter(pcap_out, append=True, sync=True)

    json_fp = None
    if save_json:
        path = json_out or (os.path.splitext(pcap_out)[0] + ".jsonl")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        json_fp = open(path, "a", encoding="utf-8")

    pkt_count = 0
    start_ts = time.time()
    print(f"[INFO] Start capture | iface={iface or 'auto'} | filter='{bpf_filter}'")
    print(f"[INFO] Writing PCAP -> {pcap_out}")
    if json_fp:
        print(f"[INFO] Writing JSONL -> {json_fp.name}")

    def _on_packet(pkt):
        nonlocal pkt_count
        pcap_writer.write(pkt)
        if json_fp:
            json_fp.write(json.dumps(packet_to_dict(pkt), ensure_ascii=False) + "\n")
        pkt_count += 1

    try:
        sniff(
            iface=iface,
            filter=bpf_filter,
            prn=_on_packet,
            store=False,
            count=max_packets if max_packets and max_packets > 0 else 0,
            timeout=timeout if timeout and timeout > 0 else None,
        )
    except PermissionError:
        _fail("패킷 캡처 권한이 없습니다. 관리자 권한으로 다시 실행하세요.\n" + _npcap_installed_hint())
    except OSError as e:
        _fail(f"인터페이스/드라이버 오류: {e}\n" + _npcap_installed_hint())
    finally:
        if json_fp:
            json_fp.close()
        pcap_writer.close()

    dur = time.time() - start_ts
    print(f"[INFO] Done. captured={pkt_count} packets in {dur:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Albion Beacon - UDP Packet Capture")
    parser.add_argument("--iface", help="캡처할 인터페이스 이름(미지정 시 자동)")
    parser.add_argument("--filter-ip", help="BPF 필터: host <IP>")
    parser.add_argument("--filter-port", type=int, help="BPF 필터: port <PORT>")
    parser.add_argument("--pcap-out", default="captures/albion_udp.pcap", help="PCAP 출력 경로")
    parser.add_argument("--save-json", action="store_true", help="JSONL 병렬 저장")
    parser.add_argument("--json-out", help="JSONL 출력 경로(미지정 시 pcap 경로 기반)")
    parser.add_argument("--max-packets", type=int, help="최대 패킷 수(없으면 무제한)")
    parser.add_argument("--timeout", type=int, help="최대 캡처 시간(초)")
    args = parser.parse_args()

    bpf = build_bpf_filter(args.filter_ip, args.filter_port)
    capture_udp(
        iface=args.iface,
        bpf_filter=bpf,
        pcap_out=args.pcap_out,
        save_json=args.save_json,
        json_out=args.json_out,
        max_packets=args.max_packets,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
