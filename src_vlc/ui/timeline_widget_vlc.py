from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMenu, QAction
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QRect, pyqtSignal, pyqtSlot, QPoint, QSize

from src.utils.time_utils import format_time_ms, format_game_time

class TimelineWidgetVLC(QWidget):
    # Signal to indicate a new position has been selected
    position_changed = pyqtSignal(int)

    def __init__(self, video_player, annotation_manager):
        super().__init__()
        self.video_player = video_player
        self.annotation_manager = annotation_manager
        self.total_duration_ms = 0
        self.current_position_ms = 0
        self.annotation_markers = []
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        self.timeline_visual = TimelineVisualVLC(self.video_player)
        self.timeline_visual.setMinimumHeight(50)
        self.timeline_visual.position_clicked.connect(self.on_position_clicked)
        self.main_layout.addWidget(self.timeline_visual)

        # For simplicity, reusing the table from your original implementation:
        self.annotation_table = QTableWidget()
        self.annotation_table.setColumnCount(5)
        self.annotation_table.setHorizontalHeaderLabels(["Time", "Game Time", "Label", "Team", ""])
        self.annotation_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.annotation_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.annotation_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.annotation_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.annotation_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.annotation_table.verticalHeader().setVisible(False)
        self.annotation_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.annotation_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.annotation_table.setAlternatingRowColors(True)
        self.annotation_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.annotation_table.customContextMenuRequested.connect(self.show_context_menu)
        self.annotation_table.cellDoubleClicked.connect(self.on_annotation_double_clicked)
        self.main_layout.addWidget(self.annotation_table)

    @pyqtSlot(int)
    def set_duration(self, duration_ms):
        self.total_duration_ms = duration_ms
        self.timeline_visual.set_total_duration(duration_ms)

    @pyqtSlot(int)
    def update_position(self, position_ms):
        self.current_position_ms = position_ms
        self.timeline_visual.set_current_position(position_ms)

    @pyqtSlot()
    def update_annotations(self):
        annotations = self.annotation_manager.get_annotations(sort_by_position=True)
        markers = []
        for annotation in annotations:
            position = int(annotation["position"])
            label = annotation["label"]
            team = annotation["team"]
            color = QColor(52, 152, 219) if team == "home" else QColor(231, 76, 60)
            markers.append({"position": position, "color": color, "label": label})
        self.timeline_visual.set_markers(markers)
        self.update_annotation_table(annotations)

    def update_annotation_table(self, annotations):
        self.annotation_table.setRowCount(0)
        for i, annotation in enumerate(annotations):
            position_ms = int(annotation["position"])
            game_time = annotation["gameTime"]
            label = annotation["label"]
            team = annotation["team"]
            self.annotation_table.insertRow(i)
            time_str = format_time_ms(position_ms)
            self.annotation_table.setItem(i, 0, QTableWidgetItem(time_str))
            self.annotation_table.setItem(i, 1, QTableWidgetItem(game_time))
            self.annotation_table.setItem(i, 2, QTableWidgetItem(label))
            self.annotation_table.setItem(i, 3, QTableWidgetItem(team.capitalize()))
            jump_item = QTableWidgetItem("Jump")
            jump_item.setTextAlignment(Qt.AlignCenter)
            self.annotation_table.setItem(i, 4, jump_item)
            # Set row background color
            bg_color = QColor(217, 236, 255) if team == "home" else QColor(255, 221, 217)
            for col in range(5):
                item = self.annotation_table.item(i, col)
                if item:
                    item.setBackground(bg_color)

    def on_position_clicked(self, position_ms):
        self.current_position_ms = position_ms
        self.position_changed.emit(position_ms)

    def on_annotation_double_clicked(self, row, column):
        position_ms = int(self.annotation_manager.get_annotations()[row]["position"])
        self.video_player.seek(position_ms)
        self.position_changed.emit(position_ms)

    def show_context_menu(self, position):
        row = self.annotation_table.rowAt(position.y())
        if row < 0:
            return
        menu = QMenu(self)
        jump_action = QAction("Jump to Position", self)
        remove_action = QAction("Remove Annotation", self)
        menu.addAction(jump_action)
        menu.addAction(remove_action)
        action = menu.exec_(self.annotation_table.viewport().mapToGlobal(position))
        if action == jump_action:
            pos_ms = int(self.annotation_manager.get_annotations()[row]["position"])
            self.video_player.seek(pos_ms)
            self.position_changed.emit(pos_ms)
        elif action == remove_action:
            self.annotation_manager.remove_annotation(row)
            self.update_annotations()

# Helper visual component for timeline:
class TimelineVisualVLC(QWidget):
    position_clicked = pyqtSignal(int)

    def __init__(self, video_player):
        super().__init__()
        self.video_player = video_player
        self.total_duration_ms = 0
        self.current_position_ms = 0
        self.markers = []
        self.marker_radius = 4
        self.background_color = QColor(240, 240, 240)
        self.timeline_color = QColor(200, 200, 200)
        self.position_color = QColor(231, 76, 60)
        self.text_color = QColor(80, 80, 80)
        self.is_dragging = False
        self.setMinimumHeight(40)
        self.setMouseTracking(True)

    def set_total_duration(self, duration_ms):
        self.total_duration_ms = max(1, duration_ms)
        self.update()

    def set_current_position(self, position_ms):
        self.current_position_ms = min(position_ms, self.total_duration_ms)
        self.update()

    def set_markers(self, markers):
        self.markers = markers
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.background_color)
        timeline_height = 10
        timeline_y = (self.height() - timeline_height) // 2
        timeline_rect = QRect(10, timeline_y, self.width() - 20, timeline_height)
        painter.fillRect(timeline_rect, self.timeline_color)
        if self.total_duration_ms > 0:
            for marker in self.markers:
                pos = marker["position"]
                color = marker["color"]
                x_pos = int(10 + (pos / self.total_duration_ms) * (self.width() - 20))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(x_pos - self.marker_radius, timeline_y - self.marker_radius, 
                                    self.marker_radius * 2, self.marker_radius * 2)
        if self.total_duration_ms > 0:
            x_pos = int(10 + (self.current_position_ms / self.total_duration_ms) * (self.width() - 20))
            painter.setPen(QPen(self.position_color, 2))
            painter.drawLine(x_pos, timeline_rect.top() - 5, x_pos, timeline_rect.bottom() + 5)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.position_color))
            painter.drawEllipse(x_pos - 5, timeline_y + (timeline_height // 2) - 5, 10, 10)
            painter.setPen(self.text_color)
            time_text = format_time_ms(self.current_position_ms)
            painter.drawText(x_pos - 30, timeline_rect.bottom() + 20, 60, 20, Qt.AlignCenter, time_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            timeline_rect = QRect(10, 0, self.width() - 20, self.height())
            if timeline_rect.contains(event.pos()):
                x_rel = event.x() - 10
                width = self.width() - 20
                pos = int((x_rel / width) * self.total_duration_ms)
                pos = max(0, min(pos, self.total_duration_ms))
                self.current_position_ms = pos
                self.update()
                self.position_clicked.emit(pos)
                self.is_dragging = True

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            x_rel = event.x() - 10
            width = self.width() - 20
            pos = int((x_rel / width) * self.total_duration_ms)
            pos = max(0, min(pos, self.total_duration_ms))
            self.current_position_ms = pos
            self.update()
            self.position_clicked.emit(pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
