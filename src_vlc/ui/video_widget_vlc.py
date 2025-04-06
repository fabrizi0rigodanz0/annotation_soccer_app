import sys
from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt

class VideoWidgetVLC(QWidget):
    def __init__(self, video_player):
        super().__init__()
        self.video_player = video_player
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(640, 360)
        # Ensure the widget has a native window handle
        self.setAttribute(Qt.WA_NativeWindow)
    
    def showEvent(self, event):
        super().showEvent(event)
        # Link VLC output to this widget
        win_id = int(self.winId())
        if sys.platform.startswith("win"):
            self.video_player.media_player.set_hwnd(win_id)
        elif sys.platform.startswith("linux"):
            self.video_player.media_player.set_xwindow(win_id)
        elif sys.platform.startswith("darwin"):
            self.video_player.media_player.set_nsobject(win_id)
