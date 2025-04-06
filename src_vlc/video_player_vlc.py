import vlc
import time
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

class VideoPlayerVLC(QThread):
    # Instead of sending raw frames, we’ll rely on VLC rendering directly.
    duration_changed = pyqtSignal(int)      # Emits total duration (ms)
    playback_finished = pyqtSignal()          # Emits when playback ends
    position_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self.video_path = None
        self.total_duration_ms = 0
        self.current_position_ms = 0
        self.is_paused = True
        self._stop = False
        self.playback_speed = 1.0

    def load_video(self, video_path):
        self.video_path = video_path
        media = self.instance.media_new(video_path)
        self.media_player.set_media(media)
        # Parse media to get duration (this might be asynchronous; adjust if needed)
        media.parse()  # Blocking call; alternatively, use parse_async() with proper handling
        self.total_duration_ms = media.get_duration()
        self.duration_changed.emit(self.total_duration_ms)
        self.current_position_ms = 0
        self.is_paused = True
        return True

    def run(self):
        self.media_player.play()
        self.is_paused = False
        # A simple loop to update the current position.
        while not self._stop:
            pos = self.media_player.get_time()
            self.current_position_ms = pos
            self.position_changed.emit(pos)
            # Sleep briefly; adjust sleep time for smoother updates
            time.sleep(0.03 / self.playback_speed)
            if pos >= self.total_duration_ms and self.total_duration_ms > 0:
                self.playback_finished.emit()
                break

    @pyqtSlot()
    def stop(self):
        self._stop = True
        self.media_player.stop()
        self.wait()

    @pyqtSlot()
    def play(self):
        self.media_player.play()
        self.is_paused = False

    @pyqtSlot()
    def pause(self):
        self.media_player.pause()
        self.is_paused = True

    @pyqtSlot(int)
    def seek(self, position_ms):
        self.media_player.set_time(position_ms)
        self.current_position_ms = position_ms

    @pyqtSlot(float)
    def set_playback_speed(self, speed):
        self.playback_speed = speed
        self.media_player.set_rate(speed)

    def get_current_position(self):
        return self.media_player.get_time()
