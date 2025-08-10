"""
- 2025-08-07 - [추가] - v0.3.0: API 클라이언트 모듈 생성
- 기능: 중앙 서버와 데이터 통신 (현재는 시뮬레이션)
- 2025-08-07 - [수정] - v0.8.0: 실제 서버 통신 기능 구현
- 기능: requests 라이브러리를 사용하여 Flask 서버와 데이터 통신
- 2025-08-08 - [수정] - v1.0.0: 위치 공유/목록 API 연동
- 2025-08-09 - [수정] - v1.5.5: 서버 선택 정보 전송
- 기능: verify_user 함수가 선택된 서버 정보를 함께 보내도록 수정
- 2025-08-09 - [수정] - v1.5.6: 서버 정보 저장 로직 변경
- 기능: register_user가 서버 정보를 보내고, verify_user는 보내지 않음
- 2025-08-09 - [수정] - v1.6.1: /get-locations API 호출 방식 변경
- 기능: get_all_users 함수가 POST 방식으로 사용자 정보를 보내도록 수정

"""
import requests

from src.config.settings import API_BASE_URL


# --- v1.6.1 수정: username 인자 추가 및 POST 방식으로 변경 ---
def get_all_users(username):
    """서버로부터 위치를 공유 중인 모든 사용자 목록을 받아옵니다."""
    url = f"{API_BASE_URL}/get-locations"
    payload = {'username': username}
    try:
        response = requests.post(url, json=payload) # GET -> POST
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except requests.exceptions.ConnectionError:
        return []

# ... (나머지 함수는 이전과 동일) ...
def register_user(username, server):
    url = f"{API_BASE_URL}/register"
    payload = {'username': username, 'server': server}
    try:
        response = requests.post(url, json=payload)
        return response.json(), response.status_code
    except requests.exceptions.ConnectionError:
        return {'error': '서버에 연결할 수 없습니다.'}, 503

def verify_user(username):
    url = f"{API_BASE_URL}/verify"
    payload = {'username': username}
    try:
        response = requests.post(url, json=payload)
        return response.json(), response.status_code
    except requests.exceptions.ConnectionError:
        return {'error': '서버에 연결할 수 없습니다.'}, 503

def send_location_data(username, zone_name, group_size):
    url = f"{API_BASE_URL}/update-location"
    payload = {'username': username, 'zone': zone_name, 'group_size': group_size}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200: return True
        else:
            print(f"서버 응답 오류: {response.json()}")
            return False
    except requests.exceptions.ConnectionError: return False