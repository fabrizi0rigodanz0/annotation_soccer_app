"""
Video Widget Module

This module defines the video display widget that renders video frames
and handles user interactions with the video display.
"""

import numpy as np
from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtGui import QPainter, QImage, QPixmap, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QRect, pyqtSlot, QPoint, QSize

from src.utils.time_utils import format_time_ms


class VideoWidget(QWidget):
    """Widget for displaying video frames"""
    
    def __init__(self, video_player):
        super().__init__()
        
        # Set up widget properties
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(640, 360)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Store reference to video player
        self.video_player = video_player
        
        # Frame data
        self.current_frame = None
        self.current_position_ms = 0
        self.frame_pixmap = None
        
        # Display settings
        self.aspect_ratio = 16/9  # Default aspect ratio
        self.show_position = True
        self.background_color = QColor(0, 0, 0)  # Black background
        
        # Initialize empty state
        self.setAutoFillBackground(False)
    
    def sizeHint(self):
        """Suggest a size based on aspect ratio"""
        width = self.width()
        height = int(width / self.aspect_ratio)
        return QSize(width, height)
    
    @pyqtSlot(np.ndarray, int)
    def update_frame(self, frame, position_ms):
        """
        Update the current frame and position
        
        Args:
            frame (numpy.ndarray): Video frame as RGB numpy array
            position_ms (int): Current position in milliseconds
        """
        self.current_frame = frame
        self.current_position_ms = position_ms
        
        # Convert numpy frame to QImage
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        
        q_image = QImage(
            frame.data, 
            width, 
            height, 
            bytes_per_line, 
            QImage.Format_RGB888
        )
        
        # Create pixmap from image
        self.frame_pixmap = QPixmap.fromImage(q_image)
        
        # Calculate aspect ratio
        self.aspect_ratio = width / height
        
        # Trigger repaint
        self.update()
    
    def paintEvent(self, event):
        """Paint the current frame on the widget"""
        painter = QPainter(self)
        
        # Fill background
        painter.fillRect(self.rect(), self.background_color)
        
        if self.frame_pixmap:
            # Calculate display rectangle maintaining aspect ratio
            display_rect = self.calculate_display_rect()
            
            # Draw the frame
            painter.drawPixmap(display_rect, self.frame_pixmap)
            
            # Draw time position
            if self.show_position:
                self.draw_position_overlay(painter, display_rect)
        else:
            # No frame available, show placeholder
            self.draw_placeholder(painter)
    
    def calculate_display_rect(self):
        """Calculate the display rectangle maintaining aspect ratio"""
        widget_width = self.width()
        widget_height = self.height()
        
        # Calculate display size maintaining aspect ratio
        if widget_width / widget_height > self.aspect_ratio:
            # Widget is wider than frame
            display_height = widget_height
            display_width = int(display_height * self.aspect_ratio)
        else:
            # Widget is taller than frame
            display_width = widget_width
            display_height = int(display_width / self.aspect_ratio)
        
        # Center the display rectangle in the widget
        x = (widget_width - display_width) // 2
        y = (widget_height - display_height) // 2
        
        return QRect(x, y, display_width, display_height)
    
    def draw_position_overlay(self, painter, display_rect):
        """Draw time position overlay"""
        # Set up font and drawing properties
        font = QFont("Arial", 12)
        painter.setFont(font)
        painter.setPen(QPen(Qt.white))
        
        # Format position as time
        position_text = format_time_ms(self.current_position_ms)
        
        # Draw text in the bottom-right corner
        padding = 10
        text_rect = painter.fontMetrics().boundingRect(position_text)
        text_x = display_rect.right() - text_rect.width() - padding
        text_y = display_rect.bottom() - padding
        
        # Draw semi-transparent background
        bg_rect = QRect(
            text_x - 5,
            text_y - text_rect.height(),
            text_rect.width() + 10,
            text_rect.height() + 5
        )
        painter.fillRect(bg_rect, QColor(0, 0, 0, 128))
        
        # Draw text
        painter.drawText(QPoint(text_x, text_y), position_text)
    
    def draw_placeholder(self, painter):
        """Draw placeholder when no video is loaded"""
        painter.setPen(QColor(200, 200, 200))
        font = QFont("Arial", 14)
        painter.setFont(font)
        
        text = "No video loaded"
        text_rect = painter.fontMetrics().boundingRect(text)
        
        x = (self.width() - text_rect.width()) // 2
        y = (self.height() - text_rect.height()) // 2
        
        painter.drawText(x, y, text)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events"""
        if event.button() == Qt.LeftButton:
            # Toggle play/pause on double-click
            if self.video_player.is_paused:
                self.video_player.play()
            else:
                self.video_player.pause()
    
    def resizeEvent(self, event):
        """Handle widget resize events"""
        super().resizeEvent(event)
        self.update()  # Trigger repaint to update the display