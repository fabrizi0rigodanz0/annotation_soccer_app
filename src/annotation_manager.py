"""
Annotation Manager Module

This module handles the storage, retrieval, and management of video annotations.
It provides functionality to save annotations to a JSON file and load them back.
"""

import json
import os
from datetime import timedelta
import time


class AnnotationManager:
    """Manages soccer video annotations"""

    # Predefined soccer-specific labels
    LABELS = [
        "GOAL", 
        "CORNER", 
        "FREE KICK", 
        "BALL RECOVERY AND COUNTER ATTACK", 
        "BUILD-UP PLAY", 
        "POSITIONAL ATTACK", 
        "SWITCHING PLAY", 
        "NO HIGHLIGHT"
    ]
    
    # Team options
    TEAMS = ["home", "away"]
    
    def __init__(self, video_path=None):
        self.video_path = video_path
        self.annotations = []
        self.annotation_file = None
        
        # If a video path is provided, set up the annotation file path
        if video_path:
            self.set_video_path(video_path)
    
    def set_video_path(self, video_path):
        """Set the video path and determine the annotation file path"""
        self.video_path = video_path
        
        # Create annotation file path by replacing the video extension with .json
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        self.annotation_file = os.path.join(video_dir, f"{video_name}_Labels.json")
        
        # Load existing annotations if the file exists
        if os.path.exists(self.annotation_file):
            self.load_annotations()
        else:
            # Initialize with empty annotations
            self.annotations = []
            self.save_annotations()
    
    def add_annotation(self, position_ms, label, team):
        """
        Add a new annotation at the specified position
        
        Args:
            position_ms (int): Position in milliseconds
            label (str): Annotation label, must be one of the predefined labels
            team (str): Team label, either "home" or "away"
        """
        # Validate inputs
        if label not in self.LABELS:
            raise ValueError(f"Label must be one of {self.LABELS}")
            
        if team not in self.TEAMS:
            raise ValueError(f"Team must be one of {self.TEAMS}")
        
        # Format the game time as "1 - MM:SS"
        game_time = self._format_game_time(position_ms)
        
        # Create the annotation entry
        annotation = {
            "gameTime": game_time,
            "label": label,
            "position": str(position_ms),  # Store as string to match required format
            "team": team,
            "visibility": "visible"
        }
        
        # Add the annotation and save to file
        self.annotations.append(annotation)
        self.save_annotations()
        
        return annotation
    
    def remove_annotation(self, index):
        """Remove an annotation by its index"""
        if 0 <= index < len(self.annotations):
            removed = self.annotations.pop(index)
            self.save_annotations()
            return removed
        return None
    
    def update_annotation(self, index, **kwargs):
        """
        Update an existing annotation with new values
        
        Args:
            index (int): Index of the annotation to update
            **kwargs: Key-value pairs of properties to update
        """
        if 0 <= index < len(self.annotations):
            # Update only the provided properties
            for key, value in kwargs.items():
                if key in self.annotations[index]:
                    self.annotations[index][key] = value
            
            # If position was updated, recalculate gameTime
            if "position" in kwargs:
                position_ms = int(kwargs["position"])
                self.annotations[index]["gameTime"] = self._format_game_time(position_ms)
            
            self.save_annotations()
            return self.annotations[index]
        return None
    
    def get_annotations(self, sort_by_position=True):
        """
        Get all annotations, optionally sorted by position
        
        Args:
            sort_by_position (bool): Whether to sort by position
        
        Returns:
            list: List of annotation dictionaries
        """
        if sort_by_position:
            return sorted(self.annotations, key=lambda x: int(x["position"]))
        return self.annotations
    
    def get_annotations_at_position(self, position_ms, tolerance_ms=500):
        """
        Get annotations at or near the specified position
        
        Args:
            position_ms (int): Position in milliseconds
            tolerance_ms (int): Tolerance window in milliseconds
        
        Returns:
            list: List of matching annotations
        """
        matches = []
        
        for annotation in self.annotations:
            anno_pos = int(annotation["position"])
            if abs(anno_pos - position_ms) <= tolerance_ms:
                matches.append(annotation)
        
        return matches
    
    def load_annotations(self):
        """Load annotations from the JSON file"""
        try:
            with open(self.annotation_file, 'r') as f:
                data = json.load(f)
                self.annotations = data.get("annotations", [])
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading annotations: {e}")
            self.annotations = []
    
    def save_annotations(self):
        """Save annotations to the JSON file"""
        if not self.annotation_file:
            raise ValueError("Annotation file path not set")
            
        data = {"annotations": self.annotations}
        
        try:
            with open(self.annotation_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving annotations: {e}")
    
    def _format_game_time(self, position_ms):
        """
        Format milliseconds as game time string ("1 - MM:SS")
        
        Args:
            position_ms (int): Position in milliseconds
        
        Returns:
            str: Formatted game time
        """
        # Always use period 1 as specified
        period = 1
        
        # Convert to seconds and format as MM:SS
        total_seconds = position_ms / 1000
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        
        return f"{period} - {minutes:02d}:{seconds:02d}"
    
    def position_from_game_time(self, game_time):
        """
        Convert game time string to position in milliseconds
        
        Args:
            game_time (str): Game time in format "1 - MM:SS"
        
        Returns:
            int: Position in milliseconds
        """
        try:
            # Parse the game time format
            parts = game_time.split(" - ")
            if len(parts) != 2:
                raise ValueError("Invalid game time format")
            
            # Extract minutes and seconds
            time_parts = parts[1].split(":")
            if len(time_parts) != 2:
                raise ValueError("Invalid time format")
            
            minutes = int(time_parts[0])
            seconds = int(time_parts[1])
            
            # Calculate milliseconds
            position_ms = (minutes * 60 + seconds) * 1000
            
            return position_ms
        except (ValueError, IndexError) as e:
            print(f"Error parsing game time: {e}")
            return 0