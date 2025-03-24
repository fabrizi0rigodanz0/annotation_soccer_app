#!/usr/bin/env python3
"""
Soccer Video Annotation Tool - Main Application Entry Point

This script launches the soccer video annotation application, allowing users
to analyze soccer videos by adding time-based annotations with customizable labels.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.ui.main_window import MainWindow


if __name__ == "__main__":
    # Enable high DPI scaling for better appearance on high-resolution displays
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create and start the application
    app = QApplication(sys.argv)
    app.setApplicationName("Soccer Video Annotator")
    app.setOrganizationName("SoccerAnalytics")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())