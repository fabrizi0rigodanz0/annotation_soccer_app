"""
Video Player Module

This module handles video playback functionality, including loading videos,
extracting frames, and controlling playback speed.
"""

import cv2
import numpy as np
import os
import time
import threading
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
        self.total_duration_ms = 0
        self.current_frame_index = 0
        self.frame_duration = 0  # Duration of a single frame in milliseconds
        
        # Playback state
        self.is_paused = True
        self.is_stopped = False
        self.playback_speed = 1.0  # Normal speed is 1.0
        
        # Performance optimization
        self.frame_buffer = []
        self.buffer_size = 20  # Increased from 5 to 20 for smoother playback
        self.prefetch_active = False
        self.adaptive_buffering = True  # Enable adaptive buffer size
        self.last_processing_times = []  # Track frame processing times
        
        # Frame skipping for performance
        self.allow_frame_skipping = True
        self.skip_threshold_ms = 10  # Skip if we're more than 10ms behind
        
        # Decoder options
        self.hw_acceleration = True
        self.last_sequential_read = -1  # For optimized sequential reading

    def load_video(self, video_path):
        """Load a video file and initialize player properties"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        # Acquire mutex to ensure thread safety
        self.mutex.lock()
        
        # Release any previously loaded video
        if self.cap is not None:
            self.cap.release()
            
        # Load the new video with hardware acceleration
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        # Try to enable hardware acceleration
        if self.hw_acceleration:
            # Try different hardware acceleration options based on OpenCV version
            try:
                # For OpenCV 4.5.1+
                self.cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
            except AttributeError:
                # Fallback for older OpenCV versions
                pass
                
            # Additional codec optimization
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
        
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
        
        # Clear frame buffer and timing data
        self.frame_buffer = []
        self.last_processing_times = []
        self.last_sequential_read = -1
        
        # Emit the duration signal
        self.duration_changed.emit(self.total_duration_ms)
        
        # Release the mutex
        self.mutex.unlock()
        
        # Start prefetching frames in the background
        self.prefetch_active = True
        
        # Start with aggressive prefetching for initial buffer
        self.prefetch_frames(high_priority=True)
        
        return True
        
    def run(self):
        """Main thread loop for video playback with adaptive frame skipping"""
        last_frame_time = time.time() * 1000  # Convert to ms
        
        while not self.is_stopped:
            self.mutex.lock()
            
            if self.is_paused:
                # Wait for play signal
                self.condition.wait(self.mutex)
                last_frame_time = time.time() * 1000  # Reset timing after pause
                    
            if not self.is_stopped and not self.is_paused:
                current_time = time.time() * 1000
                elapsed = current_time - last_frame_time
                target_frame_time = self.frame_duration / self.playback_speed
                
                # Determine if we need to skip frames to catch up
                skip_frames = False
                frames_to_skip = 0
                if self.allow_frame_skipping and elapsed > target_frame_time + self.skip_threshold_ms:
                    skip_frames = True
                    frames_behind = int((elapsed - target_frame_time) / target_frame_time)
                    # Don't skip more than 5 frames at once
                    frames_to_skip = min(frames_behind, 5)
                
                # Check if we need to read a new frame
                if self.frame_buffer and len(self.frame_buffer) > 0:
                    # Get frame from buffer
                    frame, frame_index = self.frame_buffer.pop(0)
                    self.current_frame_index = frame_index
                    
                    # Skip frames if needed
                    if skip_frames and len(self.frame_buffer) >= frames_to_skip:
                        for _ in range(frames_to_skip):
                            try:
                                frame, frame_index = self.frame_buffer.pop(0)
                                self.current_frame_index = frame_index
                            except IndexError:
                                break
                    
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
                
                # Update timing
                last_frame_time = time.time() * 1000
                    
            self.mutex.unlock()
            
            # Adjusted sleep time based on playback speed
            if not self.is_paused and not self.is_stopped:
                # Dynamically adjust sleep time to maintain timing
                current_time = time.time() * 1000
                elapsed = current_time - last_frame_time
                remaining = max(1, int((self.frame_duration / self.playback_speed) - elapsed))
                self.msleep(remaining)
                
                # Refill buffer if it's getting low
                if len(self.frame_buffer) < self.buffer_size // 2 and self.prefetch_active:
                    self.prefetch_frames()
    
    def prefetch_frames(self, high_priority=False):
        """
        Prefetch frames into buffer for smoother playback
        
        Args:
            high_priority (bool): If True, fill buffer more aggressively
        """
        if self.cap is None or not self.prefetch_active:
            return
        
        # Determine optimal buffer size based on video complexity
        if self.adaptive_buffering and len(self.last_processing_times) > 0:
            avg_processing_time = sum(self.last_processing_times) / len(self.last_processing_times)
            target_buffer = int(max(5, min(30, (avg_processing_time / (self.frame_duration / 1000)) * 2)))
            self.buffer_size = target_buffer
        
        # Use a separate thread for prefetching if high priority
        if high_priority and len(self.frame_buffer) < 3:
            def prefetch_task():
                # Read up to 5 frames immediately to prevent stutter
                for _ in range(5):
                    next_frame_index = self.current_frame_index + len(self.frame_buffer)
                    if next_frame_index >= self.total_frames:
                        break
                        
                    success, frame = self.read_frame(next_frame_index)
                    if success:
                        self.mutex.lock()
                        self.frame_buffer.append((frame, next_frame_index))
                        self.mutex.unlock()
                    else:
                        break
            
            # Start a one-off prefetch thread for immediate needs
            threading.Thread(target=prefetch_task).start()
            return
                
        # Fill buffer up to buffer_size
        start_time = time.time()
        frames_added = 0
        
        while len(self.frame_buffer) < self.buffer_size:
            next_frame_index = self.current_frame_index + len(self.frame_buffer)
            if next_frame_index >= self.total_frames:
                break
            
            frame_start_time = time.time()
            success, frame = self.read_frame(next_frame_index)
            frame_time = time.time() - frame_start_time
            
            # Track processing time for this frame to adjust buffer size
            self.last_processing_times.append(frame_time)
            if len(self.last_processing_times) > 10:
                self.last_processing_times.pop(0)
            
            if success:
                self.frame_buffer.append((frame, next_frame_index))
                frames_added += 1
            else:
                break
                
            # Don't monopolize the thread for too long
            if time.time() - start_time > 0.1:  # Max 100ms for prefetching
                break
    
    def read_frame(self, frame_index):
        """Read a specific frame from the video file with optimizations"""
        if self.cap is None:
            return False, None
            
        # Minimize seeking for sequential reads (big performance improvement)
        current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        # If this is a sequential read or we need to seek
        if frame_index == self.last_sequential_read + 1:
            # Sequential read - no need to seek, just read next frame
            success, frame = self.cap.read()
            if success:
                self.last_sequential_read = frame_index
        else:
            # Non-sequential - need to seek
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            success, frame = self.cap.read()
            if success:
                self.last_sequential_read = frame_index
        
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
        self.last_sequential_read = -1  # Reset sequential reading optimization
        
        # If paused, read and emit the frame at the new position
        if self.is_paused:
            success, frame = self.read_frame(frame_index)
            if success:
                self.last_sequential_read = frame_index
                self.frame_ready.emit(frame, position_ms)
        
        # Start refilling the buffer
        self.prefetch_active = True
        
        self.mutex.unlock()
        
        # Begin prefetching frames from the new position with high priority
        self.prefetch_frames(high_priority=True)
    
    def set_playback_speed(self, speed):
        """Set the playback speed (1.0 = normal speed)"""
        self.mutex.lock()
        self.playback_speed = max(0.25, min(speed, 10.0))  # Limit between 0.25x and 10x
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