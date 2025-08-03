import time
import datetime
from typing import Union, Tuple, Optional

def get_current_timestamp() -> int:
    """
    Get current Unix timestamp in seconds.
    
    Returns:
        Current timestamp as integer
    """
    return int(time.time())

def get_timestamp_ms() -> int:
    """
    Get current Unix timestamp in milliseconds.
    
    Returns:
        Current timestamp in milliseconds as integer
    """
    return int(time.time() * 1000)

def format_timestamp(timestamp: Optional[int] = None, 
                   format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a Unix timestamp as a human-readable string.
    
    Args:
        timestamp: Unix timestamp (defaults to current time if None)
        format_str: Format string for strftime
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = get_current_timestamp()
    return time.strftime(format_str, time.localtime(timestamp))

def format_relative_time(timestamp: int) -> str:
    """
    Format a timestamp as a relative time (e.g., "2 minutes ago").
    
    Args:
        timestamp: Unix timestamp to format
        
    Returns:
        Relative time string
    """
    now = get_current_timestamp()
    diff = now - timestamp
    
    if diff < 60:  # Less than a minute
        return "just now"
    elif diff < 3600:  # Less than an hour
        minutes = diff // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < 86400:  # Less than a day
        hours = diff // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < 604800:  # Less than a week
        days = diff // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return format_timestamp(timestamp, "%Y-%m-%d")

def is_expired(timestamp: int, ttl: int) -> bool:
    """
    Check if a timestamp has expired based on a TTL.
    
    Args:
        timestamp: Base timestamp to check
        ttl: Time-to-live in seconds
        
    Returns:
        True if expired, False otherwise
    """
    return (get_current_timestamp() - timestamp) > ttl

def get_expiry_time(ttl: int) -> int:
    """
    Calculate an expiry timestamp based on current time and TTL.
    
    Args:
        ttl: Time-to-live in seconds
        
    Returns:
        Expiry timestamp
    """
    return get_current_timestamp() + ttl

def parse_iso_timestamp(iso_str: str) -> int:
    """
    Parse an ISO 8601 timestamp string to Unix timestamp.
    
    Args:
        iso_str: ISO 8601 timestamp string (e.g., "2023-07-15T14:30:15Z")
        
    Returns:
        Unix timestamp
    """
    dt = datetime.datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    return int(dt.timestamp())

def get_time_until_next_event(last_event_time: int, interval: int) -> int:
    """
    Calculate time until next scheduled event.
    
    Args:
        last_event_time: Last event timestamp
        interval: Event interval in seconds
        
    Returns:
        Seconds until next event
    """
    elapsed = get_current_timestamp() - last_event_time
    return max(0, interval - elapsed)

def format_duration(seconds: int) -> str:
    """
    Format a duration in seconds as a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining = seconds % 3600
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{hours}h {minutes}m {seconds}s"

def get_timestamp_parts() -> Tuple[int, int, int, int, int, int]:
    """
    Get current timestamp broken into parts.
    
    Returns:
        Tuple of (year, month, day, hour, minute, second)
    """
    t = time.localtime()
    return (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

def time_id() -> str:
    """
    Generate a timestamp-based ID string.
    Useful for creating unique IDs for messages, etc.
    
    Returns:
        Timestamp-based ID string
    """
    t = get_timestamp_parts()
    return f"{t[0]}{t[1]:02d}{t[2]:02d}-{t[3]:02d}{t[4]:02d}{t[5]:02d}"