import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QAction,
    QFileDialog, QMessageBox, QSplitter, QStatusBar, QLabel, QPushButton, QToolBar
)
from PyQt5.QtCore import Qt, QSettings, QDir, QTimer, QMetaObject, Q_ARG

from src_vlc.video_player_vlc import VideoPlayerVLC
from src_vlc.ui.video_widget_vlc import VideoWidgetVLC
from src_vlc.ui.timeline_widget_vlc import TimelineWidgetVLC
from src_vlc.ui.controls_widget_vlc import ControlsWidgetVLC
from src.annotation_manager import AnnotationManager
from src.ui.annotation_panel import AnnotationPanel

class MainWindowVLC(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soccer Video Annotator VLC")
        self.setMinimumSize(1024, 768)
        self.settings = QSettings()
        self.restore_geometry()
        self.video_player = VideoPlayerVLC()
        self.video_player.start()
        self.annotation_manager = AnnotationManager()
        self.setup_ui()
        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()
        self.connect_signals()
        self.current_video_path = None
        self.auto_annotation_timer = QTimer(self)
        self.auto_annotation_timer.setInterval(3000)
        self.auto_annotation_timer.timeout.connect(self.add_automatic_annotation)
        self.auto_annotation_active = False

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_layout.addWidget(self.main_splitter)
        self.video_container = QWidget()
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_widget = VideoWidgetVLC(self.video_player)
        self.video_layout.addWidget(self.video_widget)
        self.controls_widget = ControlsWidgetVLC(self.video_player)
        self.video_layout.addWidget(self.controls_widget)
        self.main_splitter.addWidget(self.video_container)
        self.timeline_widget = TimelineWidgetVLC(self.video_player, self.annotation_manager)
        self.main_splitter.addWidget(self.timeline_widget)
        self.main_splitter.setSizes([700, 300])
        self.annotation_panel = AnnotationPanel(self.annotation_manager)
        self.annotation_panel.setVisible(False)
        self.video_layout.addWidget(self.annotation_panel)

    def create_menus(self):
        self.file_menu = self.menuBar().addMenu("&File")
        self.open_action = QAction("&Open Video...", self)
        self.open_action.triggered.connect(self.open_video)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addSeparator()
        self.exit_action = QAction("E&xit", self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        self.view_menu = self.menuBar().addMenu("&View")
        self.toggle_annotation_panel_action = QAction("&Annotation Panel", self)
        self.toggle_annotation_panel_action.setCheckable(True)
        self.toggle_annotation_panel_action.triggered.connect(self.toggle_annotation_panel)
        self.view_menu.addAction(self.toggle_annotation_panel_action)
        self.help_menu = self.menuBar().addMenu("&Help")
        self.about_action = QAction("&About", self)
        self.about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(self.about_action)

    def create_toolbars(self):
        self.main_toolbar = QToolBar("Main Toolbar")
        self.main_toolbar.setMovable(False)
        self.addToolBar(self.main_toolbar)
        self.main_toolbar.addAction(self.open_action)
        self.main_toolbar.addSeparator()
        self.add_annotation_button = QPushButton("Add Annotation")
        self.add_annotation_button.clicked.connect(self.toggle_annotation_panel)
        self.main_toolbar.addWidget(self.add_annotation_button)
        self.main_toolbar.addSeparator()
        self.auto_annotate_toggle_button = QPushButton("Auto 'NO HIGHLIGHT': OFF")
        self.auto_annotate_toggle_button.setCheckable(True)
        self.auto_annotate_toggle_button.clicked.connect(self.toggle_auto_annotation)
        self.auto_annotate_toggle_button.setEnabled(False)
        self.main_toolbar.addWidget(self.auto_annotate_toggle_button)

    def create_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.status_label = QLabel("Ready")
        self.statusbar.addWidget(self.status_label, 1)
        self.video_info_label = QLabel("")
        self.statusbar.addPermanentWidget(self.video_info_label)

    def connect_signals(self):
        self.video_player.duration_changed.connect(self.timeline_widget.set_duration)
        self.controls_widget.play_pause_toggled.connect(self.on_play_pause_toggled)
        self.annotation_panel.annotation_added.connect(self.timeline_widget.update_annotations)
        self.annotation_panel.annotation_added.connect(lambda ann: self.video_player.play())
        self.annotation_panel.annotation_canceled.connect(self.on_annotation_canceled)
        self.timeline_widget.position_changed.connect(self.controls_widget.update_position)

    def open_video(self):
        last_dir = self.settings.value("last_directory", QDir.homePath())
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", last_dir, "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*)"
        )
        if file_path:
            self.settings.setValue("last_directory", os.path.dirname(file_path))
            try:
                self.video_player.load_video(file_path)
                self.annotation_manager.set_video_path(file_path)
                self.timeline_widget.update_annotations()
                self.current_video_path = file_path
                video_name = os.path.basename(file_path)
                self.status_label.setText(f"Loaded video: {video_name}")
                self.video_info_label.setText(f"Duration: {self.video_player.total_duration_ms} ms")
                self.toggle_annotation_panel_action.setEnabled(True)
                self.add_annotation_button.setEnabled(True)
                self.auto_annotate_toggle_button.setEnabled(True)
                self.auto_annotation_active = False
                self.auto_annotate_toggle_button.setText("Auto 'NO HIGHLIGHT': OFF")
                self.auto_annotate_toggle_button.setChecked(False)
                self.auto_annotation_timer.stop()
            except Exception as e:
                QMessageBox.critical(self, "Error Opening Video", str(e))

    def toggle_annotation_panel(self, checked=None):
        if self.current_video_path is None:
            return
        if self.annotation_panel.isVisible():
            self.annotation_panel.setVisible(False)
            self.toggle_annotation_panel_action.setChecked(False)
            if self.video_player.is_paused:
                self.video_player.play()
                self.controls_widget.update_play_pause_button(False)
        else:
            self.annotation_panel.setVisible(True)
            self.toggle_annotation_panel_action.setChecked(True)
            if not self.video_player.is_paused:
                self.video_player.pause()
                self.controls_widget.update_play_pause_button(True)
            position_ms = self.video_player.get_current_position()
            self.annotation_panel.set_position(position_ms)

    def on_annotation_canceled(self):
        self.annotation_panel.setVisible(False)
        self.toggle_annotation_panel_action.setChecked(False)

    def on_play_pause_toggled(self, paused):
        if paused:
            self.video_player.pause()
            if self.auto_annotation_active:
                self.auto_annotation_timer.stop()
        else:
            self.video_player.play()
            if self.auto_annotation_active:
                self.auto_annotation_timer.start()

    def toggle_auto_annotation(self, checked):
        self.auto_annotation_active = checked
        if checked:
            self.auto_annotate_toggle_button.setText("Auto 'NO HIGHLIGHT': ON")
            if not self.video_player.is_paused:
                self.auto_annotation_timer.start()
            self.status_label.setText("Auto-annotation active: adding 'NO HIGHLIGHT' labels every 3 seconds")
        else:
            self.auto_annotate_toggle_button.setText("Auto 'NO HIGHLIGHT': OFF")
            self.auto_annotation_timer.stop()
            self.status_label.setText("Auto-annotation disabled")

    def add_automatic_annotation(self):
        if not self.current_video_path or self.annotation_panel.isVisible():
            return
        existing = self.annotation_manager.get_annotations_at_position(
            self.video_player.get_current_position(), tolerance_ms=1500
        )
        if not existing:
            annotation = self.annotation_manager.add_annotation(
                self.video_player.get_current_position(), "NO HIGHLIGHT", "home"
            )
            self.timeline_widget.update_annotations()
            self.status_label.setText(f"Auto-added 'NO HIGHLIGHT' at position {self.video_player.get_current_position()} ms")

    def show_about(self):
        QMessageBox.about(
            self, "About Soccer Video Annotator VLC",
            "Soccer Video Annotation Tool (VLC Version)\n\nA tool for annotating soccer videos with custom labels."
        )

    def restore_geometry(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1280, 800)
            frame_geometry = self.frameGeometry()
            screen_center = self.screen().availableGeometry().center()
            frame_geometry.moveCenter(screen_center)
            self.move(frame_geometry.topLeft())

    def closeEvent(self, event):
        if self.video_player:
            self.video_player.stop()
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()
