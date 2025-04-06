#!/usr/bin/env python3
"""
Soccer Video Annotator (VLC Version) - Main Application Entry Point
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src_vlc.ui.main_window_vlc import MainWindowVLC

if __name__ == "__main__":
    # Enable high DPI scaling for better appearance on high-resolution displays
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Soccer Video Annotator VLC")
    app.setOrganizationName("SoccerAnalytics")
    
    window = MainWindowVLC()
    window.show()
    
    sys.exit(app.exec_())
