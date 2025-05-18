from django import template
from django.utils.safestring import mark_safe
from datetime import timedelta

register = template.Library()

@register.filter
def safe_duration(value):
    """Convert any duration value to a safe string representation"""
    try:
        # Handle the case when it's a string
        if isinstance(value, str):
            # Try to convert from a string format HH:MM:SS
            parts = value.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                value = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            else:
                # If it's not a properly formatted duration string, return a default
                return '0:00:00'
        
        # Handle timedelta objects
        if isinstance(value, timedelta):
            total_seconds = value.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            return f"{hours}:{minutes:02d}:{seconds:02d}"
            
        # For any other type, return a default value
        return '0:00:00'
        
    except (ValueError, TypeError):
        # Return a default value if conversion fails
        return '0:00:00'
