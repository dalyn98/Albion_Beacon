"""
- 2025-08-09 - [수정] - v1.4.0: 해상도 감지 로직 분리
- 기능: 해상도를 감지하여 문자열로 반환하는 기능만 수행하도록 수정
- 2025-08-09 - [수정] - v1.5.3: 두 종류의 캡처 영역을 모두 저장
- 기능: 해상도 프리셋 적용 시 zone_name_area와 char_info_area를 모두 settings.json에 저장
- 2025-08-09 - [수정] - v2.0.1: 모든 UI 영역의 좌표를 동적으로 계산하도록 수정
- 기능: 자동 설정 시, ui_layout의 모든 키에 대해 비율 계산을 수행하고 저장
- 2025-08-09 - [수정] - v2.0.3: 프리셋 기반 자동 설정 로직으로 복원
- 기능: 비율 계산 대신, 감지된 해상도와 일치하는 프리셋을 찾아 적용

"""
import json
import pygetwindow as gw
from src.config.resolution_presets import RESOLUTION_PRESETS

SETTINGS_FILE = 'settings.json'
DEFAULT_SETTINGS = {
    'zone_name_area': None,
    'char_info_area': None
}

def load_settings():
    """설정 파일을 읽어 파이썬 딕셔너리로 반환합니다."""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_SETTINGS

def save_settings(settings):
    """파이썬 딕셔너리를 설정 파일(JSON)에 저장합니다."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def detect_resolution():
    """'Albion Online Client' 창을 직접 찾아 해상도를 감지하여 반환합니다."""
    try:
        game_window = gw.getWindowsWithTitle('Albion Online Client')[0]
        resolution_str = f"{game_window.width}x{game_window.height}"
        print(f"감지된 클라이언트 해상도: {resolution_str}")
        return resolution_str
    except IndexError:
        print("오류: 'Albion Online Client' 창을 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"해상도 감지 중 오류 발생: {e}")
        return None

def apply_auto_preset():
    """
    해상도를 감지하고, 일치하는 프리셋이 있으면 설정을 자동으로 적용합니다.
    """
    detected_res = detect_resolution()
    if detected_res and detected_res in RESOLUTION_PRESETS:
        preset = RESOLUTION_PRESETS[detected_res]
        settings = load_settings()
        settings['char_info_area'] = preset['char_info_area']
        settings['zone_name_area'] = preset['zone_name_area']
        save_settings(settings)
        return detected_res # 성공 시 감지된 해상도 반환
    return None # 실패 시 None 반환