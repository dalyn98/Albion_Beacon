"""
- 2025-08-10 - [수정] - v3.1.5: 상세 네트워크 정보 진단 도구
- 기능: psutil과 Scapy가 인식하는 모든 인터페이스의 상세 정보를 비교하여 출력
"""
import psutil
import socket
from scapy.all import conf

print("--- 1. psutil이 보는 네트워크 정보 ---")
addrs = psutil.net_if_addrs()
stats = psutil.net_if_stats()

for name, addresses in addrs.items():
    is_up = "UP" if stats.get(name) and stats[name].isup else "DOWN"
    ipv4 = "N/A"
    for addr in addresses:
        if addr.family == socket.AF_INET:
            ipv4 = addr.address
    # 보기 편하도록 정렬하여 출력
    print(f"  - 이름: {name:<25} | 상태: {is_up:<5} | IPv4: {ipv4}")

print("\n--- 2. Scapy가 보는 네트워크 정보 (conf.ifaces) ---")
if not conf.ifaces:
    print("Scapy가 인터페이스를 찾지 못했습니다. Npcap이 설치되었는지, 관리자 권한으로 실행했는지 확인해주세요.")
else:
    for iface in conf.ifaces.values():
        ipv4_list = iface.ips.get(socket.AF_INET, [])
        # 보기 편하도록 정렬하여 출력
        print(f"  - 이름: {iface.name:<50} | 설명: {iface.description:<35} | IPv4: {ipv4_list}")

print("\n--- 분석 ---")
print("1번 목록에서 찾은 활성 IP 주소가, 2번 목록의 어떤 인터페이스에 포함되어 있는지 확인해주세요.")