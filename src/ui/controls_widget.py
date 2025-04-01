"""
Controls Widget Module

This module defines the playback control widget that allows the user
to control video playback, including play/pause, seek, and speed controls.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QSlider, QStyle, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtGui import QIcon

from src.utils.time_utils import format_time_ms


class ControlsWidget(QWidget):
    """Widget for video playback controls"""
    
    # Signals
    play_pause_toggled = pyqtSignal(bool)  # Emitted when play/pause is toggled (True = paused)
    
    def __init__(self, video_player):
        super().__init__()
        
        # Store reference to video player
        self.video_player = video_player
        
        # Control state
        self.is_paused = True
        self.is_seeking = False
        
        # UI setup
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(10)
        
        # Play/Pause button
        self.play_pause_button = QPushButton()
        self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_pause_button.setIconSize(QSize(24, 24))
        self.play_pause_button.setToolTip("Play/Pause (Space)")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.main_layout.addWidget(self.play_pause_button)
        
        # Step backward button
        self.step_backward_button = QPushButton()
        self.step_backward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.step_backward_button.setToolTip("Previous Frame")
        self.step_backward_button.clicked.connect(self.video_player.step_backward)
        self.main_layout.addWidget(self.step_backward_button)
        
        # Step forward button
        self.step_forward_button = QPushButton()
        self.step_forward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.step_forward_button.setToolTip("Next Frame")
        self.step_forward_button.clicked.connect(self.video_player.step_forward)
        self.main_layout.addWidget(self.step_forward_button)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setMinimum(0)
        self.position_slider.setMaximum(1000)  # We'll scale the actual duration
        self.position_slider.setValue(0)
        self.position_slider.setTracking(True)
        self.position_slider.setToolTip("Seek")
        self.position_slider.valueChanged.connect(self.on_slider_value_changed)
        self.position_slider.sliderPressed.connect(self.on_slider_pressed)
        self.position_slider.sliderReleased.connect(self.on_slider_released)
        self.main_layout.addWidget(self.position_slider)
        
        # Position label
        self.position_label = QLabel("00:00 / 00:00")
        self.position_label.setMinimumWidth(100)
        self.main_layout.addWidget(self.position_label)
        
        # Speed control
        self.speed_label = QLabel("Speed:")
        self.main_layout.addWidget(self.speed_label)
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "1.0x", "1.5x", "2.0x","4.0x", "5.0x", "10.0x"])
        self.speed_combo.setCurrentIndex(2)  # Default to 1.0x
        self.speed_combo.currentIndexChanged.connect(self.on_speed_changed)
        self.main_layout.addWidget(self.speed_combo)
    
    def toggle_play_pause(self):
        """Toggle between play and pause states"""
        self.is_paused = not self.is_paused
        
        # Update button icon
        self.update_play_pause_button(self.is_paused)
        
        # Emit signal
        self.play_pause_toggled.emit(self.is_paused)
    
    def update_play_pause_button(self, paused):
        """Update the play/pause button based on state"""
        self.is_paused = paused
        
        if paused:
            self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
    
    @pyqtSlot(int)
    def update_position(self, position_ms):
        """Update the position display and slider"""
        if not self.is_seeking:
            # Update slider
            if self.video_player.total_duration_ms > 0:
                position_value = int((position_ms / self.video_player.total_duration_ms) * 1000)
                self.position_slider.setValue(position_value)
            
            # Update label
            current_time = format_time_ms(position_ms)
            total_time = format_time_ms(self.video_player.total_duration_ms)
            self.position_label.setText(f"{current_time} / {total_time}")
    
    def on_slider_value_changed(self, value):
        """Handle slider value changes"""
        if self.is_seeking:
            # Calculate position in milliseconds
            position_ms = int((value / 1000) * self.video_player.total_duration_ms)
            
            # Update label
            current_time = format_time_ms(position_ms)
            total_time = format_time_ms(self.video_player.total_duration_ms)
            self.position_label.setText(f"{current_time} / {total_time}")
    
    def on_slider_pressed(self):
        """Handle slider press events"""
        self.is_seeking = True
    
    def on_slider_released(self):
        """Handle slider release events"""
        # Get the slider value and convert to milliseconds
        value = self.position_slider.value()
        position_ms = int((value / 1000) * self.video_player.total_duration_ms)
        
        # Seek to the new position
        self.video_player.seek(position_ms)
        
        # End seeking mode
        self.is_seeking = False
    
    def on_speed_changed(self, index):
        """Handle playback speed changes"""
        # Get the speed value from the combo box text
        speed_text = self.speed_combo.currentText()
        speed = float(speed_text.replace('x', ''))
        
        # Set the playback speed
        self.video_player.set_playback_speed(speed)