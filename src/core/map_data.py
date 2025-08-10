"""
- 2025-08-09 - [추가] - v1.6.0: 알비온 맵 데이터 모듈
- 출처: https://github.com/broderickhyman/albion-maps-data
- 기능: 알비온 온라인의 모든 지역 연결 정보를 저장
- 2025-08-09 - [수정] - v1.6.4: 테스트용 블랙존 맵 데이터 추가
- 기능: Bridgewatch Portal 주변 블랙존 맵 정보 추가
- 2025-08-09 - [수정] - v1.6.5: 전체 지역 이름 목록 추가
- 기능: OCR 후처리용 '사전'으로 사용할 ALL_ZONES 리스트 추가

"""
ZONE_TYPES = {
    "Bridgewatch Portal": "ROYAL",
    "Sandrift Steppe": "BLACK",
    "Sandrift Coast": "BLACK",
    # ... (중략) ...
}

MAP_CONNECTIONS = {
    "Bridgewatch Portal": ["Bridgewatch", "Sandrift Steppe"],
    "Sandrift Steppe": ["Bridgewatch Portal", "Sandrift Coast"],
    "Sandrift Coast": ["Sandrift Steppe"],
    # ... (중략) ...
    "Lymhurst": ["Lymhurst Portal", "Highland Cross", "The Oolite Plain"],
    "Highland Cross": ["Lymhurst", "Dudley Cross", "Birchcopse"],
}

# --- v1.6.5 추가 ---
# ZONE_TYPES와 MAP_CONNECTIONS의 모든 지역 이름을 합쳐 중복을 제거한 '사전'
ALL_ZONES = list(set(list(ZONE_TYPES.keys()) + [zone for neighbors in MAP_CONNECTIONS.values() for zone in neighbors] + list(MAP_CONNECTIONS.keys())))