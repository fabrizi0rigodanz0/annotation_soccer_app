"""
Annotation Panel Module

This module defines the panel for creating and editing annotations.
It is displayed when the user presses the spacebar to add a new annotation.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

from src.utils.time_utils import format_time_ms, format_game_time


class AnnotationPanel(QWidget):
    """Panel for creating annotations at a specific time point"""
    
    # Signals
    annotation_added = pyqtSignal(dict)  # Emitted when an annotation is added
    annotation_canceled = pyqtSignal()  # Emitted when annotation is canceled
    
    def __init__(self, annotation_manager):
        super().__init__()
        
        # Store reference to annotation manager
        self.annotation_manager = annotation_manager
        
        # Initialize state
        self.current_position_ms = 0
        
        # Set up UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        
        # Title and time display
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("Add Annotation")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.header_layout.addWidget(self.title_label)
        
        self.time_label = QLabel()
        self.header_layout.addWidget(self.time_label, alignment=Qt.AlignRight)
        self.main_layout.addLayout(self.header_layout)
        
        # Label selection
        self.label_group = QGroupBox("Select Label")
        self.label_layout = QVBoxLayout(self.label_group)
        
        self.label_combo = QComboBox()
        self.label_combo.addItems(self.annotation_manager.LABELS)
        self.label_layout.addWidget(self.label_combo)
        
        self.main_layout.addWidget(self.label_group)
        
        # Team selection
        self.team_group = QGroupBox("Select Team")
        self.team_layout = QHBoxLayout(self.team_group)
        
        self.team_buttons = QButtonGroup(self)
        self.home_radio = QRadioButton("Home")
        self.away_radio = QRadioButton("Away")
        self.team_buttons.addButton(self.home_radio, 0)
        self.team_buttons.addButton(self.away_radio, 1)
        
        # Set default
        self.home_radio.setChecked(True)
        
        self.team_layout.addWidget(self.home_radio)
        self.team_layout.addWidget(self.away_radio)
        
        self.main_layout.addWidget(self.team_group)
        
        # Buttons
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel)
        
        self.save_button = QPushButton("Save Annotation")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.on_save)
        
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.save_button)
        
        self.main_layout.addLayout(self.button_layout)
        
        # Set fixed size for the panel
        self.setFixedHeight(self.sizeHint().height())
        
        # Style
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
            }
            #save_button {
                background-color: #4CAF50;
                color: white;
            }
        """)
    
    def set_position(self, position_ms):
        """Set the current position for annotation"""
        self.current_position_ms = position_ms
        
        # Update the time display
        time_str = format_time_ms(position_ms)
        game_time = format_game_time(position_ms)
        self.time_label.setText(f"Time: {time_str} (Game: {game_time})")
    
    def on_save(self):
        """Save the current annotation"""
        # Get the selected label
        label = self.label_combo.currentText()
        
        # Get the selected team
        team = "home" if self.home_radio.isChecked() else "away"
        
        # Add the annotation
        annotation = self.annotation_manager.add_annotation(
            self.current_position_ms,
            label,
            team
        )
        
        # Emit the signal
        self.annotation_added.emit(annotation)
        
        # Hide the panel
        self.hide()
    
    def on_cancel(self):
        """Cancel annotation creation"""
        self.annotation_canceled.emit()
        self.hide()
    
    def showEvent(self, event):
        """Handle panel show event"""
        super().showEvent(event)
        
        # Reset to default values
        self.label_combo.setCurrentIndex(0)
        self.home_radio.setChecked(True)