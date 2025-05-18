"""
Custom middleware for enhancing security, providing CSRF protection,
and fixing duration field issues.
"""
import logging
import re
from datetime import timedelta
from django.middleware.csrf import get_token
from django.utils.deprecation import MiddlewareMixin
from django.db import connections

logger = logging.getLogger(__name__)

class EnsureCsrfCookieMiddleware:
    """
    Middleware that ensures the CSRF cookie is set for every request.
    This avoids problems where the CSRF cookie may not be set 
    before a user attempts to submit a form.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the token (will set the cookie if it isn't already set)
        csrf_token = get_token(request)
        
        # Log if CSRF token is missing
        if 'csrftoken' not in request.COOKIES:
            logger.info(f"Setting CSRF cookie for path: {request.path}")
        
        response = self.get_response(request)
        return response


class DurationFieldFixMiddleware:
    """
    Middleware to fix duration fields in Django's database operations layer
    and response context data. This ensures that duration fields won't cause
    errors during database operations or template rendering.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self._patched = False
        
    def __call__(self, request):
        # Apply the database operations patch only once
        if not self._patched:
            self._patch_db_operations()
            self._patched = True
        
        # Process the request
        response = self.get_response(request)
        
        # Only process TemplateResponse objects
        if hasattr(response, 'context_data') and response.context_data:
            # Process the context data to handle any duration fields
            self._sanitize_duration_fields(response.context_data)
        
        return response
    
    def _patch_db_operations(self):
        """
        Monkey patch Django's database operations layer to safely handle duration fields
        This is applied to all database connections to ensure that all duration fields
        are handled correctly regardless of the database backend.
        """
        for connection_name in connections:
            connection = connections[connection_name]
            if hasattr(connection.ops, 'convert_durationfield_value'):
                original_convert = connection.ops.convert_durationfield_value
                
                def patched_convert_durationfield(value, expression, connection, context=None):
                    if value is None:
                        return None
                    
                    try:
                        # Try the original conversion
                        return original_convert(value, expression, connection)
                    except (TypeError, ValueError) as e:
                        logger.warning(f"Duration field conversion error: {str(e)} for value: {value}")
                        
                        # Try to handle string format HH:MM:SS
                        if isinstance(value, str):
                            try:
                                if ':' in value:
                                    parts = value.split(':')
                                    if len(parts) == 3:
                                        hours, minutes, seconds = map(int, parts)
                                        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
                            except (ValueError, TypeError):
                                pass
                                
                        # If all conversion attempts fail, return a default duration of 0
                        return timedelta(0)
                
                # Apply the patch
                connection.ops.convert_durationfield_value = patched_convert_durationfield
                logger.info(f"Patched convert_durationfield_value for connection: {connection_name}")
    
    def _patch_models(self):
        """
        Monkey patch certain models to safely handle duration fields
        """
        try:
            from accounts.models import StudentProfile
            
            # Add a safety wrapper for total_study_time access
            original_get = StudentProfile.__getattribute__
            
            def safe_getattribute(self, name):
                attr = original_get(self, name)
                if name == 'total_study_time':
                    # If it's a string, try to convert it or return a safe value
                    if isinstance(attr, str):
                        try:
                            # Try to parse as HH:MM:SS
                            if ':' in attr:
                                parts = attr.split(':')
                                if len(parts) == 3:
                                    hours, minutes, seconds = map(int, parts)
                                    return timedelta(hours=hours, minutes=minutes, seconds=seconds)
                            # If parsing fails, return zero duration
                            return timedelta(0)
                        except (ValueError, TypeError):
                            return timedelta(0)
                return attr
            
            StudentProfile.__getattribute__ = safe_getattribute
        except (ImportError, AttributeError):
            # If we can't patch, just continue
            pass
    
    def _sanitize_duration_fields(self, context, path=''):
        """
        Recursively sanitize duration fields in context data
        """
        if not context:
            return
            
        if isinstance(context, dict):
            for key, value in list(context.items()):
                if key is None or value is None:
                    continue
                    
                new_path = f"{path}.{key}" if path else key
                
                # Handle dictionary values recursively
                if isinstance(value, dict):
                    self._sanitize_duration_fields(value, new_path)
                
                # Handle list/tuple values recursively
                elif isinstance(value, (list, tuple)):
                    for i, item in enumerate(value):
                        if item is not None:
                            item_path = f"{new_path}[{i}]"
                            if isinstance(item, (dict, list, tuple)):
                                self._sanitize_duration_fields(item, item_path)
                
                # Check if this might be a duration field (by naming convention)
                elif key and (key.endswith('_time') or key.endswith('_duration') or key == 'duration'):
                    # For string duration values
                    if isinstance(value, str):
                        # Only accept properly formatted durations
                        if not re.match(r'^\d+:\d{2}:\d{2}$', value):
                            context[key] = '0:00:00'
                    # For None values
                    elif value is None:
                        context[key] = '0:00:00'
                    # Convert timedeltas to strings to avoid rendering issues
                    elif hasattr(value, 'total_seconds'):
                        # It's a timedelta object - format as string
                        total_seconds = int(value.total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        context[key] = f"{hours}:{minutes:02d}:{seconds:02d}"
