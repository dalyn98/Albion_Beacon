# api_test.py
"""

West (Americas) 서버: gameinfo.albiononline.com/api/gameinfo/

East (Asia) 서버: gameinfo-sgp.albiononline.com/api/gameinfo/

Europe 서버: gameinfo-ams.albiononline.com/api/gameinfo/
"""
import json

import requests

# 테스트할 캐릭터 이름
PLAYER_NAME = "trade02"

# 우리가 사용하려는 API 주소
url = f"gameinfo-sgp.albiononline.com/api/gameinfo/search?q={PLAYER_NAME}"

print(f"--- 1. API 요청 시작 ---")
print(f"요청 주소: {url}")

try:
    # 5초의 타임아웃을 설정하여 요청을 보냅니다.
    response = requests.get(url, timeout=5)

    print(f"\n--- 2. 서버 응답 상태 코드 확인 ---")
    print(f"Status Code: {response.status_code} {'(성공)' if response.status_code == 200 else '(실패)'}")

    print(f"\n--- 3. 서버가 보낸 원본(Raw) 텍스트 확인 ---")
    # 서버가 JSON이 아닌 다른 텍스트(예: 에러 메시지)를 보냈는지 확인하기 위해 원본을 출력합니다.
    print(response.text)

    print(f"\n--- 4. JSON 형식으로 변환 시도 ---")
    # 원본 텍스트를 JSON(파이썬 딕셔너리)으로 변환합니다.
    data = response.json()
    print("JSON 변환 성공!")

    print(f"\n--- 5. 변환된 데이터 확인 (Pretty Print) ---")
    # 보기 좋게 출력합니다.
    print(json.dumps(data, indent=2))

except requests.exceptions.RequestException as e:
    print(f"\n--- 오류 발생 ---")
    print(f"API 요청 중 네트워크 오류가 발생했습니다: {e}")
except json.JSONDecodeError:
    print(f"\n--- 오류 발생 ---")
    print("서버가 올바른 JSON 형식이 아닌 응답을 보냈습니다.")