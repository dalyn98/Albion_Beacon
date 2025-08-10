"""
- 2025-08-07 - [추가] - v0.1.0: GUI 모듈 생성
- 기능: PyQt5를 이용한 메인 윈도우 및 위젯(버튼, 라벨 등) 생성

- 2025-08-07 - [수정] - v0.3.0: 자동 공유 스레드 기능 추가
- 기능: 백그라운드 스레드를 이용한 주기적인 위치 캡처 및 서버 전송

- 2025-08-07 - [수정] - v0.4.0: 캡처 영역 설정 기능 연동
- 기능: '캡처 영역 설정' 버튼 및 관련 로직 추가
- 2025-08-07 - [수정] - v0.5.1: 캡처 이미지 미리보기 기능 추가
- 기능: 수동 캡처 시, 캡처된 이미지를 GUI에 직접 표시하여 OCR 디버깅을 돕는다.
- 2025-08-07 - [수정] - v0.6.0: 자동 공유 루프 로직 최신화
- 기능: share_location_thread가 안정적인 캡처 및 OCR 로직을 사용하도록 수정
- 2025-08-07 - [수정] - v0.8.0: 사용자 인증 UI 및 서버 연동
- 기능: 탭 위젯 도입, 인증 탭 UI 및 등록/코드요청 기능 구현
- 2025-08-07 - [수정] - v0.9.0: 사용자 인증 UI 및 서버 연동
- 기능: 탭 위젯 도입, 인증 탭 UI 및 등록/코드요청/인증확인 기능 구현
- 2025-08-08 - [수정] - v1.0.0: 실시간 사용자 목록 표시 기능 구현
- 2025-08-08 - [수정] - v1.2.0: 상호작용 버튼 유무로 인증 로직 최종 변경
- 2025-08-08 - [수정] - v1.2.1: 최종 인증 로직 적용
- 2025-08-09 - [수정] - v1.4.0: 자동 제안 및 사용자 확인 기반의 해상도 설정
- 기능: 프로그램 시작 시 해상도를 자동 제안하고, 사용자의 선택에 따라 설정을 적용
- 2025-08-09 - [수정] - v1.4.2: '최초 1회 자동 설정 + 상시 수동 변경' 방식 적용
- 기능: 팝업 확인창을 제거하고, 해상도 설정 UI를 항상 활성화
- 2025-08-09 - [수정] - v1.5.1: 사용자 목록에 길드 컬럼 추가
- 기능: 사용자 목록 테이블에 길드 이름을 표시하도록 UI 및 로직 수정
- 2025-08-09 - [수정] - v1.5.2: 사용자 목록에 본인 위치 하이라이트 기능 추가
- 기능: 사용자 목록 최상단에 자신의 위치를 고정하고 배경색으로 강조 표시
- 2025-08-09 - [수정] - v1.5.3: 인증/위치 캡처 영역 분리
- 기능: 인증 시 char_info_area를, 위치 공유 시 zone_name_area를 사용하도록 수정
- 2025-08-09 - [수정] - v1.5.5: 서버 선택 기능 추가
- 기능: 사용자 인증 시 서버를 선택하는 UI 추가 및 관련 로직 수정
- 2025-08-09 - [수정] - v1.5.6: 서버 정보 저장 로직 변경
- 기능: '등록' 시에만 서버 정보를 전송하도록 UI 로직 수정
- 2025-08-09 - [수정] - v1.6.1: 누락된 함수 추가 및 API 호출 방식 수정
- 기능: 누락된 share_location_thread 함수를 복원하고, get_all_users 호출 방식을 수정
- 2025-08-09 - [수정] - v1.6.7: 드롭다운 메뉴 표시 오류 수정
- 기능: 해상도 프리셋 콤보박스가 올바른 키 값을 표시하도록 수정
- 2025-08-09 - [수정] - v2.0.0: 프로젝트 구조 리팩토링 적용
- 기능: 변경된 디렉터리 구조에 맞게 모든 import 경로 수정
- 2025-08-09 - [수정] - v2.0.2: 리팩토링 후 import 경로 및 로직 수정
- 기능: 변경된 settings_manager의 함수를 올바르게 호출하도록 수정

"""

import sys
import time
import re
from threading import Thread, Event
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,
                             QLineEdit, QGridLayout, QTabWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QHBoxLayout, QComboBox, QMessageBox)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QCoreApplication, pyqtSignal, QObject

# OCR 기능은 인증에만 사용
from src.core.capture import capture_screen_area
from src.core.ocr import ocr_for_authentication
# 새로운 네트워크 리스너 임포트
from src.client.capture_controls import UdpCaptureController
from src.client.api_client import register_user, verify_user, send_location_data, get_all_users
from src.config.settings import SHARE_INTERVAL_SECONDS, API_SERVERS
from src.client.area_selector import AreaSelector
from src.config.settings_manager import save_settings, load_settings, detect_resolution
from src.config.resolution_presets import RESOLUTION_PRESETS
from src.core.env_guard import NpcapMissingError
from unicodedata import normalize

class WorkerSignals(QObject):
    update_status = pyqtSignal(str)
    update_user_list = pyqtSignal(list)


class AlbionBeaconApp(QWidget):
    def __init__(self):
        super().__init__()
        self.capture = UdpCaptureController()
        self.is_sharing = False
        self.worker_thread = None
        self.capture_stop_event = Event()
        self.signals = WorkerSignals()
        self.selector_window = None
        self.authenticated_user = None
        self.initUI()
        self.check_initial_settings()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        self.share_tab = QWidget()
        self.auth_tab = QWidget()
        tabs.addTab(self.share_tab, "위치 공유")
        tabs.addTab(self.auth_tab, "사용자 인증")
        self.setup_share_tab()
        self.setup_auth_tab()
        self.setWindowTitle('Albion Beacon v3.2.0')
        self.setGeometry(300, 300, 500, 500)
        self.show()

    def setup_share_tab(self):
        grid = QGridLayout(self.share_tab)
        self.status_label = QLabel('상태: 초기 설정 확인 중...')
        self.current_res_label = QLabel("현재 적용된 설정: 없음")

        self.resolution_label = QLabel("해상도 프리셋 (인증용):")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(RESOLUTION_PRESETS.keys())
        self.apply_preset_button = QPushButton("선택 해상도로 적용")
        self.setup_capture_button = QPushButton('인증 영역 수동 설정')

        self.share_button = QPushButton('위치 공유 시작')
        self.group_size_label = QLabel('현재 그룹 인원:')
        self.group_size_input = QLineEdit('1')

        self.user_table = QTableWidget()
        # 거리(칸) 컬럼은 패킷 분석 기능 구현 전까지 임시 제거
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(['캐릭터명', '길드', '위치', '인원', '마지막 갱신'])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        grid.addWidget(self.status_label, 0, 0, 1, 2)
        grid.addWidget(self.current_res_label, 1, 0, 1, 2)
        grid.addWidget(self.resolution_label, 2, 0)
        grid.addWidget(self.resolution_combo, 2, 1)
        grid.addWidget(self.apply_preset_button, 3, 0, 1, 2)
        grid.addWidget(self.setup_capture_button, 4, 0, 1, 2)
        grid.addWidget(self.group_size_label, 5, 0)
        grid.addWidget(self.group_size_input, 5, 1)
        grid.addWidget(self.share_button, 6, 0, 1, 2)
        grid.addWidget(self.user_table, 7, 0, 1, 2)

        self.share_button.clicked.connect(self.toggle_sharing)
        self.setup_capture_button.clicked.connect(self.open_area_selector)
        self.signals.update_status.connect(self.update_status_label)
        self.signals.update_user_list.connect(self.update_user_table)
        self.apply_preset_button.clicked.connect(self.apply_manual_preset)

    def setup_auth_tab(self):
        layout = QGridLayout(self.auth_tab)
        self.auth_status_label = QLabel("인증 상태: 미인증")
        self.server_label = QLabel("게임 서버:")
        self.server_combo = QComboBox()
        self.server_combo.addItems(API_SERVERS.keys())
        self.username_label = QLabel("알비온 캐릭터 이름:")
        self.username_input = QLineEdit()
        self.register_button = QPushButton("서버에 캐릭터 등록")
        self.verify_button = QPushButton("본인인증 실행")
        layout.addWidget(self.auth_status_label, 0, 0, 1, 2)
        layout.addWidget(self.server_label, 1, 0)
        layout.addWidget(self.server_combo, 1, 1)
        layout.addWidget(self.username_label, 2, 0)
        layout.addWidget(self.username_input, 2, 1)
        layout.addWidget(self.register_button, 3, 0, 1, 2)
        layout.addWidget(self.verify_button, 4, 0, 1, 2)
        self.register_button.clicked.connect(self.register_user_button_clicked)
        self.verify_button.clicked.connect(self.verify_user_button_clicked)

    def check_initial_settings(self):
        settings = load_settings()
        # 인증 영역만 확인하여, 해상도 프리셋이 적용되었는지 검사
        if settings.get('char_info_area'):
            self.status_label.setText("상태: 저장된 설정 불러오기 완료.")
            self.update_current_res_label()
            return

        # 설정이 없으면 자동 제안 (팝업은 제거됨)
        detected_res = detect_resolution()
        if detected_res and detected_res in RESOLUTION_PRESETS:
            self.status_label.setText(f"상태: '{detected_res}' 해상도가 감지되어 자동 적용되었습니다.")
            self.apply_preset(detected_res)
        else:
            self.status_label.setText("상태: 지원하는 해상도가 아닙니다. 수동으로 선택해주세요.")
            self.current_res_label.setText("현재 적용된 설정: 없음")

    def update_current_res_label(self):
        settings = load_settings()
        current_char_info = tuple(settings.get('char_info_area')) if settings.get('char_info_area') else None
        if not current_char_info:
            self.current_res_label.setText("현재 적용된 설정: 없음")
            return

        for res, data in RESOLUTION_PRESETS.items():
            if current_char_info == tuple(data['char_info_area']):
                self.current_res_label.setText(f"현재 적용된 설정: {res} (프리셋)")
                return
        self.current_res_label.setText("현재 적용된 설정: 사용자 지정")

    def apply_preset(self, resolution_str):
        preset = RESOLUTION_PRESETS.get(resolution_str)
        if preset:
            settings = load_settings()
            # 인증 영역 좌표만 저장 (위치 좌표는 더 이상 사용 안 함)
            settings['char_info_area'] = preset['char_info_area']
            # 기존 zone_name_area는 제거하거나 남겨둘 수 있음 (일단 남겨둠)
            if 'zone_name_area' in settings:
                del settings['zone_name_area']
            save_settings(settings)
            self.status_label.setText(f"상태: {resolution_str} 프리셋 적용 완료.")
            self.update_current_res_label()
        else:
            self.status_label.setText("오류: 선택된 프리셋을 찾을 수 없습니다.")

    def apply_manual_preset(self):
        selected_resolution = self.resolution_combo.currentText()
        self.apply_preset(selected_resolution)

    def register_user_button_clicked(self):
        username = self.username_input.text().strip()
        server = self.server_combo.currentText()
        if not username:
            self.auth_status_label.setText("오류: 캐릭터 이름을 입력해주세요.")
            return

        self.auth_status_label.setText(f"'{username}' ({server}) 등록 시도 중...")
        QCoreApplication.processEvents()
        data, status_code = register_user(username, server)

        if status_code == 201:
            self.auth_status_label.setText(f"'{username}' 등록 성공! 이제 본인인증을 실행하세요.")
        elif status_code == 200:
            self.auth_status_label.setText(f"'{username}' 서버 정보 업데이트 완료. 본인인증을 실행하세요.")
        else:
            self.auth_status_label.setText(f"등록 오류: {data.get('error', '알 수 없는 오류')}")

    def verify_user_button_clicked(self):
        username_to_verify = self.username_input.text().strip()
        if not username_to_verify:
            self.auth_status_label.setText("오류: 인증할 캐릭터 이름을 입력해주세요.")
            return
        self.auth_status_label.setText("캐릭터 정보 창을 캡처하여 분석합니다...")
        QCoreApplication.processEvents()
        pil_image = capture_screen_area(area_key='char_info_area')

        if not pil_image:
            self.auth_status_label.setText("인증 실패: 화면 캡처에 실패했습니다.")
            return

        full_text_from_screen = ocr_for_authentication(pil_image)
        text_lower = " ".join(normalize("NFKD", full_text_from_screen).casefold().split())
        other_player_keywords = ['whisper', 'mail', 'friend', '귓속말', '메일', '친구', 'invitar', 'susurrar']
        has_other_keywords = any(keyword in text_lower for keyword in other_player_keywords)
        is_name_found = username_to_verify.lower() in text_lower

        if not has_other_keywords and is_name_found:
            self.auth_status_label.setText("본인 확인 성공! 서버에 최종 인증을 요청합니다...")
            QCoreApplication.processEvents()

            data, status_code = verify_user(username_to_verify)

            if status_code == 200:
                self.authenticated_user = username_to_verify
                self.auth_status_label.setText(f"'{username_to_verify}'님 최종 인증 성공!")
                self.username_input.setEnabled(False)
                self.register_button.setEnabled(False)
                self.verify_button.setEnabled(False)
                self.server_combo.setEnabled(False)
            else:
                self.auth_status_label.setText(f"서버 오류: {data.get('error', '알 수 없는 오류')}")
        else:
            self.auth_status_label.setText("인증 실패: 본인 캐릭터 정보 창이 아니거나, 이름을 찾을 수 없습니다.")
            print(f"--- 인증 실패 디버그 정보 ---")
            print(f"OCR 결과: {full_text_from_screen}")
            print(f"타인 키워드 발견 여부: {has_other_keywords}")
            print(f"입력한 이름 발견 여부: {is_name_found}")
            print(f"--------------------------")

    def toggle_sharing(self):
        """'위치 공유 시작/중단' 버튼이 네트워크 캡처 스레드를 제어합니다."""
        if not self.is_sharing:
            if not self.authenticated_user:
                self.status_label.setText("오류: 위치 공유를 시작하려면 먼저 인증해야 합니다.")
                return

            self.is_sharing = True
            self.capture_stop_event.clear()
            self.share_button.setText('위치 공유 중단')
            self.status_label.setText('상태: 네트워크 캡처 시작 중...')

            self.worker_thread = Thread(
                target=start_capture,
                args=(self.capture_stop_event,),
                daemon=True
            )
            self.worker_thread.start()
            self.status_label.setText('상태: 위치 공유 중 (네트워크 감시 중)')
        else:
            self.is_sharing = False
            self.capture_stop_event.set()
            self.share_button.setText('위치 공유 시작')
            self.status_label.setText('상태: 공유 중단됨.')

    def open_area_selector(self):
        if not self.selector_window or not self.selector_window.isVisible():
            self.selector_window = AreaSelector()
            self.selector_window.area_selected.connect(self.on_area_selected)
            self.selector_window.show()

    def on_area_selected(self, area_coords):
        settings = load_settings()
        # 수동 설정은 인증 영역에만 적용
        settings['char_info_area'] = area_coords
        save_settings(settings)
        self.status_label.setText('상태: 인증 영역이 수동으로 저장되었습니다.')
        self.update_current_res_label()

    def update_status_label(self, message):
        self.status_label.setText(message)

    def update_user_table(self, users):
        me = None
        other_users = []
        for user in users:
            if user.get('username') == self.authenticated_user:
                me = user
            else:
                other_users.append(user)

        self.user_table.setRowCount(len(users))
        current_row = 0
        if me:
            self.user_table.setItem(current_row, 0, QTableWidgetItem(me.get('username', '')))
            self.user_table.setItem(current_row, 1, QTableWidgetItem(me.get('guild_name', '')))
            self.user_table.setItem(current_row, 2, QTableWidgetItem(me.get('zone', '')))
            self.user_table.setItem(current_row, 3, QTableWidgetItem(str(me.get('group_size', ''))))
            self.user_table.setItem(current_row, 4, QTableWidgetItem(me.get('last_updated', '')))
            for col in range(5):
                self.user_table.item(current_row, col).setBackground(QColor(220, 255, 220))
            current_row += 1
        for user in other_users:
            self.user_table.setItem(current_row, 0, QTableWidgetItem(user.get('username', '')))
            self.user_table.setItem(current_row, 1, QTableWidgetItem(user.get('guild_name', '')))
            self.user_table.setItem(current_row, 2, QTableWidgetItem(user.get('zone', '')))
            self.user_table.setItem(current_row, 3, QTableWidgetItem(str(user.get('group_size', ''))))
            self.user_table.setItem(current_row, 4, QTableWidgetItem(user.get('last_updated', '')))
            current_row += 1

    def toggle_capture(self):
        try:
            self._runner.start_capture(...)
        except NpcapMissingError as e:
            QMessageBox.warning(self, "Npcap Required", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AlbionBeaconApp()
    sys.exit(app.exec_())