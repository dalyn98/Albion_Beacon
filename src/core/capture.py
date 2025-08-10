"""
- 2025-08-07 - [추가] - v0.1.0: 화면 캡처 모듈 생성
- 기능: 설정된 좌표의 화면 영역을 캡처하여 파일로 저장
- 2025-08-07 - [수정] - v0.4.0: 사용자 정의 좌표 사용
- 기능: settings.json에서 캡처 좌표를 읽어와 사용하도록 변경
- 2025-08-07 - [수정] - v0.5.0: 창 지정 캡처 기능으로 변경
- 기능: pygetwindow와 pywin32를 사용하여 비활성/가려진 창도 캡처
- 2025-08-07 - [수정] - v0.5.2: 메모리 직접 처리
- 기능: 캡처 이미지를 파일로 저장하지 않고, Pillow 이미지 객체로 직접 반환
- 2025-08-07 - [수정] - v0.5.5: PrintWindow를 이용한 캡처 안정성 향상
- 기능: BitBlt 대신 PrintWindow API를 사용하여 가려진 창의 캡처 성공률을 높임
- 2025-08-07 - [수정] - v0.5.7: ctypes를 이용한 PrintWindow 직접 호출
- 기능: pywin32 라이브러리 버그를 우회하기 위해 ctypes로 직접 API 호출
- 2025-08-09 - [수정] - v1.5.3: 범용 캡처 함수로 변경
- 기능: area_key를 인자로 받아, settings.json에 저장된 특정 영역을 캡처
"""
import ctypes

import pygetwindow as gw
import win32gui
import win32ui
from PIL import Image

from src.config.settings_manager import load_settings

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()


def capture_screen_area(area_key):
    """
    settings.json에서 지정된 area_key에 해당하는 영역을 캡처합니다.
    (예: 'zone_name_area', 'char_info_area')
    """
    settings = load_settings()
    capture_area = settings.get(area_key)
    if not capture_area:
        print(f"오류: '{area_key}' 캡처 영역이 설정되지 않았습니다.")
        return None

    try:
        game_window = gw.getWindowsWithTitle('Albion Online Client')[0]
    except IndexError:
        print("오류: 'Albion Online Client' 창을 찾을 수 없습니다.")
        return None

    hwnd = game_window._hWnd

    # GetClientRect는 전체 창 크기를 반환하므로, 실제 캡처는 지정된 좌표로 수행
    left, top, right, bot = win32gui.GetClientRect(hwnd)
    w_full = right - left
    h_full = bot - top

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w_full, h_full)

    saveDC.SelectObject(saveBitMap)

    result = user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)

    if result != 1:
        print(f"경고: PrintWindow가 완벽하게 성공하지 못했습니다. (결과 코드: {result})")

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    # 전체 창 이미지에서 사용자가 선택한 영역을 잘라냅니다.
    x, y, w, h = capture_area
    cropped_im = im.crop((x, y, x + w, y + h))

    return cropped_im