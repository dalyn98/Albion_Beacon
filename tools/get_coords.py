# get_coords.py
import time

import pyautogui

print("마우스 좌표 확인 프로그램입니다. 5초 후에 시작됩니다...")
print("확인하고 싶은 위치에 마우스를 올리고 멈추세요. (Ctrl+C로 종료)")
time.sleep(5)

try:
    while True:
        x, y = pyautogui.position()
        position_str = f"X: {x}, Y: {y}"
        # 현재 줄에 덮어쓰기 위해 \r을 사용합니다.
        print(position_str, end='\r')
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\n프로그램을 종료합니다.")