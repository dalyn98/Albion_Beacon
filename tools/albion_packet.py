from scapy.all import sniff, get_working_if, UDP

# Albion Online 기본 UDP 포트 (Photon Engine)
ALBION_PORT = 5055

def packet_callback(packet):
    if UDP in packet and (packet[UDP].sport == ALBION_PORT or packet[UDP].dport == ALBION_PORT):
        print("="*50)
        print(f"[Packet] {packet[0][1].src} → {packet[0][1].dst}")
        print(f"Source Port: {packet[UDP].sport} | Dest Port: {packet[UDP].dport}")
        print(f"Length: {len(packet)} bytes")
        print("Raw Data:", bytes(packet[UDP].payload).hex())
        print("="*50)

if __name__ == "__main__":
    # 현재 동작 중인 기본 네트워크 인터페이스 자동 인식
    iface = get_working_if()
    print(f"[INFO] Capturing on interface: {iface}")

    # 관리자 권한 필요
    sniff(iface=iface, prn=packet_callback, store=False)
