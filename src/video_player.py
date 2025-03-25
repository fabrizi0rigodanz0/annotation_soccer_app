"""
Video Player Module

This module handles video playback functionality, including loading videos,
extracting frames, and controlling playback speed.
"""

import cv2
import numpy as np
import os
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition


class VideoPlayer(QThread):
    """
    Video player class that runs in a separate thread to ensure smooth playback
    """
    # Signals to communicate with the UI
    frame_ready = pyqtSignal(np.ndarray, int)  # Emits the current frame and position
    duration_changed = pyqtSignal(int)  # Emits the total duration in milliseconds
    playback_finished = pyqtSignal()  # Emits when playback reaches the end
    
    def __init__(self):
        super().__init__()
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        
        # Video properties
        self.video_path = None
        self.cap = None
        self.fps = 0
        self.total_frames = 0
        self.total_duration_ms = 0  # Adding this to fix slider issue
        self.current_frame_index = 0
        self.frame_duration = 0  # Duration of a single frame in milliseconds
        
        # Playback state
        self.is_paused = True
        self.is_stopped = False
        self.playback_speed = 1.0  # Normal speed is 1.0
        
        # Performance optimization
        self.frame_buffer = []
        self.buffer_size = 5  # Buffer 5 frames for smoother playback
        self.prefetch_active = False

    def load_video(self, video_path):
        """Load a video file and initialize player properties"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        # Acquire mutex to ensure thread safety
        self.mutex.lock()
        
        # Release any previously loaded video
        if self.cap is not None:
            self.cap.release()
            
        # Load the new video
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        # Get video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_duration = 1000 / self.fps  # Duration in milliseconds
        
        # Calculate total duration in milliseconds
        self.total_duration_ms = int((self.total_frames / self.fps) * 1000)
        
        # Reset playback state
        self.current_frame_index = 0
        self.is_paused = True
        self.is_stopped = False
        
        # Clear frame buffer
        self.frame_buffer = []
        
        # Emit the duration signal
        self.total_duration_ms = int((self.total_frames / self.fps) * 1000)  # Duration in milliseconds
        self.duration_changed.emit(self.total_duration_ms)
        
        # Release the mutex
        self.mutex.unlock()
        
        # Start prefetching frames in the background
        self.prefetch_active = True
        self.prefetch_frames()
        
        return True
        
    def run(self):
        """Main thread loop for video playback"""
        while not self.is_stopped:
            self.mutex.lock()
            
            if self.is_paused:
                # Wait for play signal
                self.condition.wait(self.mutex)
                
            if not self.is_stopped and not self.is_paused:
                # Check if we need to read a new frame
                if self.frame_buffer and len(self.frame_buffer) > 0:
                    # Get frame from buffer
                    frame, frame_index = self.frame_buffer.pop(0)
                    self.current_frame_index = frame_index
                    
                    # Calculate current position in milliseconds
                    position_ms = int(self.current_frame_index * self.frame_duration)
                    
                    # Emit the frame
                    self.frame_ready.emit(frame, position_ms)
                    
                    # Check if we've reached the end
                    if self.current_frame_index >= self.total_frames - 1:
                        self.playback_finished.emit()
                        self.is_paused = True
                else:
                    # If buffer is empty, read directly (less optimal)
                    success, frame = self.read_frame(self.current_frame_index)
                    if success:
                        # Calculate current position in milliseconds
                        position_ms = int(self.current_frame_index * self.frame_duration)
                        
                        # Emit the frame
                        self.frame_ready.emit(frame, position_ms)
                        
                        # Move to next frame
                        self.current_frame_index += 1
                        
                        # Check if we've reached the end
                        if self.current_frame_index >= self.total_frames - 1:
                            self.playback_finished.emit()
                            self.is_paused = True
                    else:
                        # Error reading frame or end of video
                        self.playback_finished.emit()
                        self.is_paused = True
                
                # Sleep to maintain proper playback speed
                sleep_time = self.frame_duration / self.playback_speed
                
            self.mutex.unlock()
            
            # Adjusted sleep time based on playback speed
            if not self.is_paused and not self.is_stopped:
                sleep_time_ms = int(self.frame_duration / self.playback_speed)
                self.msleep(max(1, sleep_time_ms))  # Ensure at least 1ms sleep to prevent CPU overload
                
                # Refill buffer if it's getting low
                if len(self.frame_buffer) < 2 and self.prefetch_active:
                    self.prefetch_frames()
    
    def prefetch_frames(self):
        """Prefetch frames into buffer for smoother playback"""
        if self.cap is None or not self.prefetch_active:
            return
            
        # Fill buffer up to buffer_size
        while len(self.frame_buffer) < self.buffer_size:
            next_frame_index = self.current_frame_index + len(self.frame_buffer)
            if next_frame_index >= self.total_frames:
                break
                
            success, frame = self.read_frame(next_frame_index)
            if success:
                self.frame_buffer.append((frame, next_frame_index))
            else:
                break
    
    def read_frame(self, frame_index):
        """Read a specific frame from the video file"""
        if self.cap is None:
            return False, None
            
        # Set the frame position
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        
        # Read the frame
        success, frame = self.cap.read()
        
        # Convert from BGR to RGB for PyQt
        if success:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
        return success, frame
    
    def play(self):
        """Start or resume video playback"""
        self.mutex.lock()
        self.is_paused = False
        self.condition.wakeAll()
        self.mutex.unlock()
    
    def pause(self):
        """Pause video playback"""
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()
    
    def stop(self):
        """Stop video playback and release resources"""
        self.mutex.lock()
        self.is_paused = True
        self.is_stopped = True
        self.prefetch_active = False
        self.condition.wakeAll()
        self.mutex.unlock()
        
        # Wait for thread to finish
        self.wait()
        
        # Release the video capture resource
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def seek(self, position_ms):
        """Seek to a specific position in the video (in milliseconds)"""
        if self.cap is None:
            return
            
        self.mutex.lock()
        
        # Calculate the frame index from milliseconds
        frame_index = int(position_ms / self.frame_duration)
        
        # Ensure the index is within bounds
        frame_index = max(0, min(frame_index, self.total_frames - 1))
        
        # Update current frame index
        self.current_frame_index = frame_index
        
        # Clear the buffer since we're moving to a new position
        self.frame_buffer = []
        
        # If paused, read and emit the frame at the new position
        if self.is_paused:
            success, frame = self.read_frame(frame_index)
            if success:
                self.frame_ready.emit(frame, position_ms)
        
        # Start refilling the buffer
        self.prefetch_active = True
        
        self.mutex.unlock()
        
        # Begin prefetching frames from the new position
        self.prefetch_frames()
    
    def set_playback_speed(self, speed):
        """Set the playback speed (1.0 = normal speed)"""
        self.mutex.lock()
        self.playback_speed = max(0.25, min(speed, 4.0))  # Limit between 0.25x and 4x
        self.mutex.unlock()
    
    def get_current_position(self):
        """Get the current position in milliseconds"""
        return int(self.current_frame_index * self.frame_duration)
    
    def step_forward(self):
        """Step forward one frame"""
        if self.cap is None:
            return
            
        self.mutex.lock()
        
        if self.current_frame_index < self.total_frames - 1:
            self.current_frame_index += 1
            success, frame = self.read_frame(self.current_frame_index)
            if success:
                position_ms = int(self.current_frame_index * self.frame_duration)
                self.frame_ready.emit(frame, position_ms)
        
        self.mutex.unlock()
    
    def step_backward(self):
        """Step backward one frame"""
        if self.cap is None:
            return
            
        self.mutex.lock()
        
        if self.current_frame_index > 0:
            self.current_frame_index -= 1
            success, frame = self.read_frame(self.current_frame_index)
            if success:
                position_ms = int(self.current_frame_index * self.frame_duration)
                self.frame_ready.emit(frame, position_ms)
        
        self.mutex.unlock()