from django import template
from django.utils.safestring import mark_safe
from datetime import timedelta
import re

register = template.Library()

@register.filter
def format_duration(value):
    """
    Template filter to safely format a duration field value
    and handle invalid duration values by returning a default.
    """
    try:
        # If value is None, return default
        if value is None:
            return '0:00:00'
            
        # If value is a string, try to parse it
        if isinstance(value, str):
            # Check if it's already in HH:MM:SS format
            if re.match(r'^\d+:\d{2}:\d{2}$', value):
                return value
                
            # Check if it's in MM:SS format and convert to HH:MM:SS
            if re.match(r'^\d+:\d{2}$', value):
                parts = value.split(':')
                return f"0:{parts[0]}:{parts[1]}"
                
            # If it's a numeric string, treat as seconds
            if value.isdigit():
                seconds = int(value)
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                return f"{hours}:{minutes:02d}:{secs:02d}"
                
            # If it's not a valid format, return default
            return '0:00:00'
        
        # If it's a timedelta object, format it
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours}:{minutes:02d}:{seconds:02d}"
            
        # If it's a number (int/float), treat as seconds
        if isinstance(value, (int, float)):
            total_seconds = int(value)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours}:{minutes:02d}:{seconds:02d}"
            
        # Any other type, return default
        return '0:00:00'
            
    except (ValueError, TypeError, AttributeError) as e:
        # In case of any error, return a safe default
        return '0:00:00'
        
@register.filter
def duration_safe(value):
    """
    A defensive wrapper around any duration field to ensure it never breaks templates.
    This should be used on any DurationField value in templates.
    """
    try:
        # Try to format it properly
        return format_duration(value)
    except Exception:
        # If anything goes wrong, return a default value
        return '0:00:00'
