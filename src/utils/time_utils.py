"""
Time Utilities Module

This module provides utility functions for time formatting and conversion
between different time representations used in the video annotation tool.
"""

def format_time_ms(milliseconds):
    """
    Format milliseconds as HH:MM:SS.mmm
    
    Args:
        milliseconds (int): Time in milliseconds
        
    Returns:
        str: Formatted time string
    """
    # Ensure non-negative value
    milliseconds = max(0, milliseconds)
    
    # Calculate components
    ms = milliseconds % 1000
    seconds = (milliseconds // 1000) % 60
    minutes = (milliseconds // (1000 * 60)) % 60
    hours = milliseconds // (1000 * 60 * 60)
    
    # Format based on whether hours are needed
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"
    else:
        return f"{minutes:02d}:{seconds:02d}.{ms:03d}"

def format_time_compact(milliseconds):
    """
    Format milliseconds as MM:SS
    
    Args:
        milliseconds (int): Time in milliseconds
        
    Returns:
        str: Formatted time string without milliseconds
    """
    # Ensure non-negative value
    milliseconds = max(0, milliseconds)
    
    # Calculate components
    seconds = (milliseconds // 1000) % 60
    minutes = (milliseconds // (1000 * 60))
    
    return f"{minutes:02d}:{seconds:02d}"

def format_game_time(milliseconds):
    """
    Format milliseconds as game time (1 - MM:SS)
    
    Args:
        milliseconds (int): Time in milliseconds
        
    Returns:
        str: Formatted game time string
    """
    # Always use period 1 as specified in requirements
    period = 1
    
    # Calculate minutes and seconds
    total_seconds = milliseconds / 1000
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    
    return f"{period} - {minutes:02d}:{seconds:02d}"

def parse_time_code(time_code):
    """
    Parse a time code string into milliseconds
    
    Args:
        time_code (str): Time code in format "HH:MM:SS.mmm" or "MM:SS.mmm"
        
    Returns:
        int: Time in milliseconds, or 0 if invalid format
    """
    try:
        parts = time_code.split(":")
        
        if len(parts) == 3:  # HH:MM:SS.mmm
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split(".")
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            
            return hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds
            
        elif len(parts) == 2:  # MM:SS.mmm
            minutes = int(parts[0])
            seconds_parts = parts[1].split(".")
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            
            return minutes * 60000 + seconds * 1000 + milliseconds
            
    except (ValueError, IndexError):
        return 0
        
    return 0

def parse_game_time(game_time):
    """
    Parse a game time string into milliseconds
    
    Args:
        game_time (str): Game time in format "1 - MM:SS"
        
    Returns:
        int: Time in milliseconds, or 0 if invalid format
    """
    try:
        # Split into period and time parts
        parts = game_time.split(" - ")
        if len(parts) != 2:
            return 0
            
        # Parse the time part
        time_parts = parts[1].split(":")
        if len(time_parts) != 2:
            return 0
            
        minutes = int(time_parts[0])
        seconds = int(time_parts[1])
        
        # Calculate milliseconds (ignoring period as per requirements)
        return minutes * 60000 + seconds * 1000
        
    except (ValueError, IndexError):
        return 0