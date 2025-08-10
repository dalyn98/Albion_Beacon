"""
- 2025-08-07 - [추가] - v0.1.0: 메인 실행 파일 생성
- 기능: 애플리케이션의 시작점(Entry Point). GUI를 실행시킴.
- 2025-08-09 - [수정] - v2.0.2: main.py 역할 단순화
- 기능: 설정 적용 로직을 gui.py로 이전하고, GUI 실행 역할만 담당

"""
import sys
from PyQt5.QtWidgets import QApplication
from src.client.gui import AlbionBeaconApp

if __name__ == '__main__':
    # 설정 적용 로직은 이제 gui.py가 담당합니다.
    app = QApplication(sys.argv)
    ex = AlbionBeaconApp()
    sys.exit(app.exec_())