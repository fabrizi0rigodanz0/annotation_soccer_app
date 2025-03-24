"""
Main Window Module

This module defines the main application window and its layout.
It integrates all UI components and manages application-level events.
"""

import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QAction, QFileDialog, QMessageBox, QSplitter,
    QStatusBar, QLabel, QPushButton, QToolBar
)
from PyQt5.QtCore import Qt, QSettings, QSize, QDir
from PyQt5.QtGui import QIcon, QKeySequence

from src.video_player import VideoPlayer
from src.annotation_manager import AnnotationManager
from src.ui.video_widget import VideoWidget
from src.ui.annotation_panel import AnnotationPanel
from src.ui.timeline_widget import TimelineWidget
from src.ui.controls_widget import ControlsWidget


class MainWindow(QMainWindow):
    """Main window for the soccer video annotation application"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize window properties
        self.setWindowTitle("Soccer Video Annotator")
        self.setMinimumSize(1024, 768)
        
        # Initialize settings
        self.settings = QSettings()
        self.restore_geometry()
        
        # Create the video player and annotation manager
        self.video_player = VideoPlayer()
        self.video_player.start()  # Start the video player thread
        self.annotation_manager = AnnotationManager()
        
        # Setup UI components
        self.setup_ui()
        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()
        
        # Setup key event handling
        self.installEventFilter(self)
        
        # Connect signals and slots
        self.connect_signals()
        
        # Initialize with empty state
        self.current_video_path = None
    
    def setup_ui(self):
        """Set up the main UI components and layout"""
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create splitter for video and timeline areas
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_layout.addWidget(self.main_splitter)
        
        # Create video area
        self.video_container = QWidget()
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create video widget
        self.video_widget = VideoWidget(self.video_player)
        self.video_layout.addWidget(self.video_widget)
        
        # Create controls widget
        self.controls_widget = ControlsWidget(self.video_player)
        self.video_layout.addWidget(self.controls_widget)
        
        # Add the video container to the splitter
        self.main_splitter.addWidget(self.video_container)
        
        # Create timeline widget
        self.timeline_widget = TimelineWidget(self.video_player, self.annotation_manager)
        self.main_splitter.addWidget(self.timeline_widget)
        
        # Set splitter proportions
        self.main_splitter.setSizes([700, 200])  # 70% video, 30% timeline
        
        # Create annotation panel (hidden by default)
        self.annotation_panel = AnnotationPanel(self.annotation_manager)
        self.annotation_panel.setVisible(False)
        self.video_layout.addWidget(self.annotation_panel)
    
    def create_menus(self):
        """Create the application menus"""
        # File menu
        self.file_menu = self.menuBar().addMenu("&File")
        
        # Open video action
        self.open_action = QAction("&Open Video...", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self.open_video)
        self.file_menu.addAction(self.open_action)
        
        self.file_menu.addSeparator()
        
        # Exit action
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut(QKeySequence.Quit)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        # View menu
        self.view_menu = self.menuBar().addMenu("&View")
        
        # Toggle annotation panel action
        self.toggle_annotation_panel_action = QAction("&Annotation Panel", self)
        self.toggle_annotation_panel_action.setShortcut("Space")
        self.toggle_annotation_panel_action.setCheckable(True)
        self.toggle_annotation_panel_action.triggered.connect(self.toggle_annotation_panel)
        self.view_menu.addAction(self.toggle_annotation_panel_action)
        
        # Help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        
        # About action
        self.about_action = QAction("&About", self)
        self.about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(self.about_action)
    
    def create_toolbars(self):
        """Create application toolbars"""
        # Main toolbar
        self.main_toolbar = QToolBar("Main Toolbar")
        self.main_toolbar.setMovable(False)
        self.addToolBar(self.main_toolbar)
        
        # Add actions to toolbar
        self.main_toolbar.addAction(self.open_action)
        self.main_toolbar.addSeparator()
        
        # Add annotation button
        self.add_annotation_button = QPushButton("Add Annotation (Space)")
        self.add_annotation_button.clicked.connect(self.toggle_annotation_panel)
        self.main_toolbar.addWidget(self.add_annotation_button)
    
    def create_statusbar(self):
        """Create the status bar"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # Status message label
        self.status_label = QLabel("Ready")
        self.statusbar.addWidget(self.status_label, 1)
        
        # Video info label
        self.video_info_label = QLabel("")
        self.statusbar.addPermanentWidget(self.video_info_label)
    
    def connect_signals(self):
        """Connect signals between components"""
        # Video player signals
        self.video_player.frame_ready.connect(self.video_widget.update_frame)
        self.video_player.frame_ready.connect(lambda frame, pos: self.timeline_widget.update_position(pos))
        self.video_player.duration_changed.connect(self.timeline_widget.set_duration)
        
        # Annotation panel signals
        self.annotation_panel.annotation_added.connect(self.timeline_widget.update_annotations)
        self.annotation_panel.annotation_canceled.connect(self.on_annotation_canceled)
        
        # Timeline widget signals
        self.timeline_widget.position_changed.connect(self.controls_widget.update_position)
        
        # Controls widget signals
        self.controls_widget.play_pause_toggled.connect(self.on_play_pause_toggled)
    
    def open_video(self):
        """Open a video file"""
        # Get last used directory
        last_dir = self.settings.value("last_directory", QDir.homePath())
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video",
            last_dir,
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*)"
        )
        
        if file_path:
            # Save the directory for next time
            self.settings.setValue("last_directory", os.path.dirname(file_path))
            
            try:
                # Load the video
                self.video_player.load_video(file_path)
                
                # Set up the annotation manager for this video
                self.annotation_manager.set_video_path(file_path)
                
                # Update the timeline with annotations
                self.timeline_widget.update_annotations()
                
                # Update status
                self.current_video_path = file_path
                video_name = os.path.basename(file_path)
                self.status_label.setText(f"Loaded video: {video_name}")
                self.video_info_label.setText(f"FPS: {self.video_player.fps:.2f} | Frames: {self.video_player.total_frames}")
                
                # Enable UI elements
                self.toggle_annotation_panel_action.setEnabled(True)
                self.add_annotation_button.setEnabled(True)
                
            except Exception as e:
                QMessageBox.critical(self, "Error Opening Video", str(e))
    
    def toggle_annotation_panel(self, checked=None):
        """Toggle the annotation panel visibility"""
        if self.current_video_path is None:
            return
            
        # If already visible, hide it
        if self.annotation_panel.isVisible():
            self.annotation_panel.setVisible(False)
            self.toggle_annotation_panel_action.setChecked(False)
            
            # Resume playback if it was paused
            if self.video_player.is_paused:
                self.video_player.play()
                self.controls_widget.update_play_pause_button(False)  # Not paused
        else:
            # Otherwise show it and pause the video
            self.annotation_panel.setVisible(True)
            self.toggle_annotation_panel_action.setChecked(True)
            
            # Pause playback
            if not self.video_player.is_paused:
                self.video_player.pause()
                self.controls_widget.update_play_pause_button(True)  # Paused
            
            # Set the current position for the annotation
            position_ms = self.video_player.get_current_position()
            self.annotation_panel.set_position(position_ms)
    
    def on_annotation_canceled(self):
        """Handle annotation cancellation"""
        self.annotation_panel.setVisible(False)
        self.toggle_annotation_panel_action.setChecked(False)
    
    def on_play_pause_toggled(self, paused):
        """Handle play/pause state changes"""
        if paused:
            self.video_player.pause()
        else:
            self.video_player.play()
    
    def show_about(self):
        """Show the about dialog"""
        QMessageBox.about(
            self,
            "About Soccer Video Annotator",
            "Soccer Video Annotation Tool\n\n"
            "A tool for annotating soccer videos with custom labels.\n\n"
            "Press spacebar to add annotations at the current position."
        )
    
    def restore_geometry(self):
        """Restore window geometry from settings"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size and position
            self.resize(1280, 800)
            self.center_on_screen()
    
    def center_on_screen(self):
        """Center the window on the screen"""
        frame_geometry = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop the video player thread
        if self.video_player:
            self.video_player.stop()
        
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())
        
        # Accept the event and close the window
        event.accept()
    
    def eventFilter(self, obj, event):
        """Custom event filter for key presses"""
        if event.type() == event.KeyPress:
            # Check for spacebar press
            if event.key() == Qt.Key_Space:
                # Only if a video is loaded
                if self.current_video_path is not None:
                    self.toggle_annotation_panel()
                    return True  # Event handled
        
        # Pass event to default handler
        return super().eventFilter(obj, event)