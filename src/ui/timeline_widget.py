"""
Timeline Widget Module

This module defines the timeline widget that displays the video timeline
and annotations, allowing navigation and visualization of annotations.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu, QAction
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QRect, pyqtSignal, pyqtSlot, QPoint, QSize

from src.utils.time_utils import format_time_ms, format_game_time


class TimelineWidget(QWidget):
    """Widget that displays video timeline and annotations"""
    
    # Signals
    position_changed = pyqtSignal(int)  # Emitted when timeline position changes
    
    def __init__(self, video_player, annotation_manager):
        super().__init__()
        
        # Store references
        self.video_player = video_player
        self.annotation_manager = annotation_manager
        
        # Timeline properties
        self.total_duration_ms = 0
        self.current_position_ms = 0
        
        # Annotation markers
        self.annotation_markers = []
        
        # UI setup
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        
        # Create timeline visualization
        self.timeline_visual = TimelineVisual(self.video_player)
        self.timeline_visual.setMinimumHeight(50)
        self.timeline_visual.position_clicked.connect(self.on_position_clicked)
        self.main_layout.addWidget(self.timeline_visual)
        
        # Create annotation table
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
        """Set the total video duration"""
        self.total_duration_ms = duration_ms
        self.timeline_visual.set_total_duration(duration_ms)
    
    @pyqtSlot(int)
    def update_position(self, position_ms):
        """Update the current playback position"""
        self.current_position_ms = position_ms
        self.timeline_visual.set_current_position(position_ms)
    
    @pyqtSlot()
    def update_annotations(self):
        """Update the annotations display"""
        # Get all annotations
        annotations = self.annotation_manager.get_annotations(sort_by_position=True)
        
        # Update markers for timeline visual
        markers = []
        for annotation in annotations:
            position = int(annotation["position"])
            label = annotation["label"]
            team = annotation["team"]
            
            # Determine marker color based on team
            color = QColor(52, 152, 219) if team == "home" else QColor(231, 76, 60)
            
            markers.append({
                "position": position,
                "color": color,
                "label": label
            })
        
        # Update timeline visual
        self.timeline_visual.set_markers(markers)
        
        # Update table
        self.update_annotation_table(annotations)
    
    def update_annotation_table(self, annotations):
        """Update the annotation table with current annotations"""
        # Clear the table
        self.annotation_table.setRowCount(0)
        
        # Add annotations to table
        for i, annotation in enumerate(annotations):
            position_ms = int(annotation["position"])
            game_time = annotation["gameTime"]
            label = annotation["label"]
            team = annotation["team"]
            
            # Add a new row
            self.annotation_table.insertRow(i)
            
            # Add time item
            time_str = format_time_ms(position_ms)
            time_item = QTableWidgetItem(time_str)
            self.annotation_table.setItem(i, 0, time_item)
            
            # Add game time item
            game_time_item = QTableWidgetItem(game_time)
            self.annotation_table.setItem(i, 1, game_time_item)
            
            # Add label item
            label_item = QTableWidgetItem(label)
            self.annotation_table.setItem(i, 2, label_item)
            
            # Add team item
            team_item = QTableWidgetItem(team.capitalize())
            self.annotation_table.setItem(i, 3, team_item)
            
            # Add jump button
            jump_item = QTableWidgetItem("Jump")
            jump_item.setTextAlignment(Qt.AlignCenter)
            self.annotation_table.setItem(i, 4, jump_item)
            
            # Set row color based on team
            if team == "home":
                for col in range(self.annotation_table.columnCount()):
                    item = self.annotation_table.item(i, col)
                    if item:
                        item.setBackground(QColor(217, 236, 255))  # Light blue for home
            else:
                for col in range(self.annotation_table.columnCount()):
                    item = self.annotation_table.item(i, col)
                    if item:
                        item.setBackground(QColor(255, 221, 217))  # Light red for away
    
    def on_position_clicked(self, position_ms):
        # Update position and seek via a queued connection
        self.current_position_ms = position_ms
        self.position_changed.emit(position_ms)
        from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(
            self.video_player, 
            "seek", 
            Qt.QueuedConnection, 
            Q_ARG(int, position_ms)
        )
    
    def on_annotation_double_clicked(self, row, column):
        """Handle double click on an annotation in the table"""
        # Get the annotation position
        position_ms = int(self.annotation_manager.get_annotations()[row]["position"])
        from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(
            self.video_player,
            "seek",
            Qt.QueuedConnection,
         Q_ARG(int, position_ms)
        )
        self.position_changed.emit(position_ms)
    
    def show_context_menu(self, position):
        """Show context menu for annotations"""
        # Get the row under the cursor
        row = self.annotation_table.rowAt(position.y())
        if row < 0:
            return
            
        # Create menu
        menu = QMenu(self)
        
        # Add actions
        jump_action = QAction("Jump to Position", self)
        remove_action = QAction("Remove Annotation", self)
        
        menu.addAction(jump_action)
        menu.addAction(remove_action)
        
        # Show menu and handle selection
        action = menu.exec_(self.annotation_table.viewport().mapToGlobal(position))
        
        if action == jump_action:
            # Jump to annotation position
            position_ms = int(self.annotation_manager.get_annotations()[row]["position"])
            self.video_player.seek(position_ms)
            self.position_changed.emit(position_ms)
            
        elif action == remove_action:
            # Remove annotation
            self.annotation_manager.remove_annotation(row)
            self.update_annotations()


class TimelineVisual(QWidget):
    """Visual timeline widget with position indicator and annotation markers"""
    
    # Signals
    position_clicked = pyqtSignal(int)  # Emitted when user clicks on timeline
    
    def __init__(self, video_player):
        super().__init__()
        
        # Store video player reference
        self.video_player = video_player
        
        # Timeline properties
        self.total_duration_ms = 0
        self.current_position_ms = 0
        self.markers = []
        self.marker_radius = 4
        
        # Colors
        self.background_color = QColor(240, 240, 240)
        self.timeline_color = QColor(200, 200, 200)
        self.position_color = QColor(231, 76, 60)  # Red
        self.text_color = QColor(80, 80, 80)
        
        # Interaction state
        self.is_dragging = False
        
        # Set fixed height
        self.setMinimumHeight(40)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
    
    def set_total_duration(self, duration_ms):
        """Set the total timeline duration"""
        self.total_duration_ms = max(1, duration_ms)  # Avoid division by zero
        self.update()
    
    def set_current_position(self, position_ms):
        """Set the current playback position"""
        self.current_position_ms = min(position_ms, self.total_duration_ms)
        self.update()
    
    def set_markers(self, markers):
        """Set annotation markers"""
        self.markers = markers
        self.update()
    
    def paintEvent(self, event):
        """Paint the timeline"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), self.background_color)
        
        # Calculate timeline rectangle
        timeline_height = 10
        timeline_y = (self.height() - timeline_height) // 2
        timeline_rect = QRect(10, timeline_y, self.width() - 20, timeline_height)
        
        # Draw timeline
        painter.fillRect(timeline_rect, self.timeline_color)
        
        # Draw markers
        if self.total_duration_ms > 0:
            for marker in self.markers:
                position = marker["position"]
                color = marker["color"]
                
                # Calculate x position
                x_pos = int(10 + (position / self.total_duration_ms) * (self.width() - 20))
                
                # Draw marker
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(x_pos - self.marker_radius, timeline_y - self.marker_radius, 
                                   self.marker_radius * 2, self.marker_radius * 2)
        
        # Draw current position indicator
        if self.total_duration_ms > 0:
            x_pos = int(10 + (self.current_position_ms / self.total_duration_ms) * (self.width() - 20))
            
            # Draw position line
            painter.setPen(QPen(self.position_color, 2))
            painter.drawLine(x_pos, timeline_rect.top() - 5, x_pos, timeline_rect.bottom() + 5)
            
            # Draw position knob
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.position_color))
            painter.drawEllipse(x_pos - 5, timeline_y + (timeline_height // 2) - 5, 10, 10)
            
            # Draw time text
            painter.setPen(self.text_color)
            time_text = format_time_ms(self.current_position_ms)
            painter.drawText(x_pos - 30, timeline_rect.bottom() + 20, 60, 20, 
                            Qt.AlignCenter, time_text)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            # Check if click is within the timeline area
            timeline_rect = QRect(10, 0, self.width() - 20, self.height())
            if timeline_rect.contains(event.pos()):
                # Calculate position
                x_rel = event.x() - 10
                width = self.width() - 20
                position = int((x_rel / width) * self.total_duration_ms)
                position = max(0, min(position, self.total_duration_ms))
                
                # Update position
                self.current_position_ms = position
                self.update()
                
                # Emit signal
                self.position_clicked.emit(position)
                
                # Start dragging
                self.is_dragging = True
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.is_dragging:
            # Calculate position
            x_rel = event.x() - 10
            width = self.width() - 20
            position = int((x_rel / width) * self.total_duration_ms)
            position = max(0, min(position, self.total_duration_ms))
            
            # Update position
            self.current_position_ms = position
            self.update()
            
            # Emit signal
            self.position_clicked.emit(position)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False