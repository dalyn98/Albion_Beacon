"""
- 2025-08-07 - [추가] - v0.4.0: 캡처 영역 선택기
- 기능: 사용자가 마우스로 화면 영역을 드래그하여 선택하는 UI
"""
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtWidgets import QWidget


class AreaSelector(QWidget):
    # 영역 선택이 완료되면 (x, y, w, h) 튜플을 포함하는 시그널을 보냄
    area_selected = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.begin = None
        self.end = None

        # 전체 화면으로, 프레임 없는 투명한 창 설정
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)

        self.setCursor(Qt.CrossCursor)  # 마우스 커서를 십자 모양으로
        print("캡처할 영역을 마우스로 드래그 해주세요. (ESC 키로 취소)")

    def paintEvent(self, event):
        """창을 그리거나 업데이트할 때 호출되는 함수"""
        painter = QPainter(self)

        # 반투명한 검은색 배경
        painter.setBrush(QBrush(QColor(0, 0, 0, 120)))
        painter.drawRect(self.rect())

        if self.begin is None or self.end is None:
            return

        # 선택된 영역만 투명하게 만듦 (배경을 지움)
        selection_rect = QRect(self.begin, self.end).normalized()
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.drawRect(selection_rect)

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        if self.begin is not None and self.end is not None:
            selection_rect = QRect(self.begin, self.end).normalized()
            # 선택된 영역의 좌표를 시그널로 보냄
            self.area_selected.emit((
                selection_rect.x(),
                selection_rect.y(),
                selection_rect.width(),
                selection_rect.height()
            ))
        self.close()

    def keyPressEvent(self, event):
        # ESC 키를 누르면 창을 닫음
        if event.key() == Qt.Key_Escape:
            self.close()