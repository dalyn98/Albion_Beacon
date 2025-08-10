"""
- 2025-08-07 - [추가] - v0.1.0: 초기 설정 파일 생성
- 2025-08-07 - [수정] - v0.3.0: 서버 및 공유 주기 설정 추가
- 기능: 화면 캡처 좌표 등 주요 설정값 관리
- 2025-08-07 - [수정] - v0.4.0: 고정 좌표 제거
- 2025-08-09 - [수정] - v1.5.5: 서버별 API 주소 추가
- 기능: East, West, Europe 서버의 API 엔드포인트 관리

"""

# 기존 설정값들
SCREENSHOT_PATH = "../../zone_screenshot.png"
TESSERACT_CMD_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
API_BASE_URL = "http://127.0.0.1:5000"
SHARE_INTERVAL_SECONDS = 15
OCR_FAIL_TOLERANCE = 4


# --- v1.5.5 추가 ---
API_SERVERS = {
    'East (Asia)': 'https://gameinfo-sgp.albiononline.com/api/gameinfo',
    'West (Americas)': 'https://gameinfo.albiononline.com/api/gameinfo',
    'Europe': 'https://gameinfo-ams.albiononline.com/api/gameinfo',
}