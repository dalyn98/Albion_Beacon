"""
- 2025-08-09 - [추가] - v1.6.0: 맵 거리 계산 로직
- 기능: 너비 우선 탐색(BFS) 알고리즘을 사용하여 두 지역 간의 최단 거리 계산
- 2025-08-10 - [수정] - v2.2.0: JSON 데이터 파일 연동
- 기능: map_data.json 파일을 읽어 맵 데이터를 불러오도록 수정

"""
import json
from collections import deque

from src.core.map_data import MAP_CONNECTIONS

try:
    with open('src/core/map_data.json', 'r', encoding='utf-8') as f:
        map_data = json.load(f)
    ZONE_TYPES = map_data.get("ZONE_TYPES", {})
    MAP_CONNECTIONS = map_data.get("MAP_CONNECTIONS", {})
except (FileNotFoundError, json.JSONDecodeError):
    print("오류: map_data.json 파일을 찾을 수 없거나 파일이 손상되었습니다.")
    ZONE_TYPES = {}
    MAP_CONNECTIONS = {}

# 양방향 그래프 생성 (이전과 동일)
graph = {}
for zone, neighbors in MAP_CONNECTIONS.items():
    if zone not in graph: graph[zone] = []
    for neighbor in neighbors:
        if neighbor not in graph: graph[neighbor] = []
        graph[zone].append(neighbor)
        graph[neighbor].append(zone)

def get_distance(start_zone, end_zone):
    # ... (이하 get_distance 함수 내용은 이전과 동일) ...
    if start_zone == end_zone:
        return 0
    start_type = ZONE_TYPES.get(start_zone)
    end_type = ZONE_TYPES.get(end_zone)
    if not start_type or not end_type:
        return "알 수 없음"
    if start_type != end_type:
        return "블랙존" if end_type == "BLACK" else "로얄 대륙"
    if start_zone not in graph or end_zone not in graph:
        return "알 수 없음"
    queue = deque([(start_zone, 0)])
    visited = {start_zone}
    while queue:
        current_zone, distance = queue.popleft()
        for neighbor in graph.get(current_zone, []):
            if neighbor == end_zone:
                return distance + 1
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    return "경로 없음"