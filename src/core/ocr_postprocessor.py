"""
- 2025-08-09 - [추가] - v1.6.5: OCR 후처리기
- 기능: 레벤슈타인 거리를 사용하여 OCR 결과와 가장 유사한 텍스트를 사전에서 찾음
- 2025-08-10 - [수정] - v2.2.0: JSON 데이터 파일 연동
- 기능: map_data.json 파일을 읽어 ALL_ZONES '사전'을 생성
"""
import Levenshtein
import json
from src.core.map_data import ALL_ZONES


try:
    with open('src/core/map_data.json', 'r', encoding='utf-8') as f:
        map_data = json.load(f)
    ZONE_TYPES = map_data.get("ZONE_TYPES", {})
    MAP_CONNECTIONS = map_data.get("MAP_CONNECTIONS", {})
    ALL_ZONES = list(set(list(ZONE_TYPES.keys()) + [zone for neighbors in MAP_CONNECTIONS.values() for zone in neighbors] + list(MAP_CONNECTIONS.keys())))
except (FileNotFoundError, json.JSONDecodeError):
    print("오류: map_data.json 파일을 찾을 수 없거나 파일이 손상되었습니다.")
    ALL_ZONES = []


def find_best_match(ocr_text):
    # ... (이하 find_best_match 함수 내용은 이전과 동일) ...
    if not ocr_text:
        return None
    ocr_text_normalized = "".join(ocr_text.split()).lower()
    best_match = None
    lowest_distance = float('inf')
    for zone_name in ALL_ZONES:
        zone_name_normalized = "".join(zone_name.split()).lower()
        distance = Levenshtein.distance(ocr_text_normalized, zone_name_normalized)
        if distance < lowest_distance:
            lowest_distance = distance
            best_match = zone_name
    threshold = len(ocr_text_normalized) * 0.3
    if lowest_distance <= threshold:
        return best_match
    else:
        print(f"후처리 실패: '{ocr_text}'와 가장 유사한 '{best_match}'를 찾았으나, 신뢰도가 낮아 폐기합니다. (거리: {lowest_distance})")
        return None