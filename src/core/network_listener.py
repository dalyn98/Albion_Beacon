"""
- 2025-08-10 - [추가] - v3.0.0: 네트워크 리스너 기본 프레임워크
- 기능: pyshark를 사용하여 알비온 온라인의 네트워크 트래픽을 캡처하고 출력
- 2025-08-10 - [수정] - v3.0.1: 네트워크 인터페이스 자동 감지
- 기능: psutil을 사용하여 활성 네트워크 인터페이스를 자동으로 찾아 사용
- 2025-08-10 - [수정] - v3.1.0: Scapy를 이용한 네트워크 캡처
- 기능: Wireshark 의존성을 제거하고 Scapy를 사용하여 트래픽 캡처
- 2025-08-10 - [수정] - v3.1.1: Scapy npcap 로딩 오류 수정
- 기능: 최신 Scapy 버전에 맞춰 불필요한 load_contrib 코드 제거
- 2025-08-10 - [수정] - v3.1.2: AF_INET 속성 오류 수정
- 기능: psutil.AF_INET 대신 올바른 socket.AF_INET을 사용하도록 수정
- 2025-08-10 - [수정] - v3.1.3: Scapy 인터페이스 이름 불일치 문제 해결
- 기능: psutil과 Scapy의 인터페이스를 IP 주소 기준으로 매칭하여 정확도 향상
- 2025-08-10 - [수정] - v3.1.4: Scapy ImportError 해결
- 기능: get_windows_if_list 대신 conf.ifaces를 사용하여 인터페이스 검색
- 2025-08-10 - [수정] - v3.1.5: 인터페이스 이름 직접 매칭 방식으로 변경
- 기능: Scapy의 IP 조회 문제를 우회하기 위해, psutil이 찾은 이름을 직접 사용
- 2025-08-10 - [수정] - v3.1.6: pcap 라이브러리로 최종 전환
- 기능: albiondata-client와 유사한 pcap 라이브러리를 사용하여 안정성 확보
- 2025-8-10 - [수정] - v3.2.0: pypcap 라이브러리로 최종 전환
- 기능: pcap-ct의 access violation 오류를 해결하기 위해 pypcap 사용

"""
from scapy.all import sniff, get_working_if, UDP, Raw

# Albion Online Photon Engine UDP 포트
ALBION_PORT = 5055


def process_packet(packet):
    """캡처된 각 패킷에 대해 실행될 콜백 함수입니다."""
    # UDP 레이어와 Raw 데이터(payload)가 있는지 확인
    if UDP in packet and Raw in packet:
        # payload를 16진수 문자열로 변환하여 출력
        payload_hex = bytes(packet[UDP].payload).hex()

        # TODO: 여기에 payload_hex를 분석하여 위치 정보를 추출하는 코드가 들어갈 예정
        print(f"캡처된 UDP Payload: {payload_hex[:100]}...")  # 너무 길기 때문에 앞 100자만 출력


def start_capture(stop_event):
    """
    활성 인터페이스에서 트래픽 캡처를 시작합니다.
    GUI의 중단 신호를 받기 위해 stop_event를 인자로 받습니다.
    """
    try:
        iface = get_working_if()
        if not iface:
            print("오류: 활성화된 네트워크 인터페이스를 찾을 수 없습니다.")
            return

        print(f"'{iface.name}' 인터페이스에서 UDP 포트 {ALBION_PORT} 트래픽 캡처를 시작합니다...")

        # sniff 함수는 blocking 함수이므로, stop_event가 설정될 때까지 실행됩니다.
        sniff(
            iface=iface.name,
            filter=f"udp port {ALBION_PORT}",
            prn=process_packet,
            store=False,
            stop_filter=lambda p: stop_event.is_set()  # stop_event가 설정되면 캡처 중단
        )
        print("네트워크 캡처가 정상적으로 중단되었습니다.")

    except Exception as e:
        print(f"\n캡처 중 오류 발생: {e}")
        print("Npcap이 올바르게 설치되었는지, 스크립트가 관리자 권한으로 실행 중인지 확인해주세요.")