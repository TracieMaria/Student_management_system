"""
Custom database initialization middleware that runs at the very beginning of request processing
to ensure all database connections are properly patched before any ORM operations.
"""
from datetime import timedelta
import logging
from django.db import connections

logger = logging.getLogger(__name__)

class DatabaseInitMiddleware:
    """
    Middleware to initialize and patch database connections at the very beginning
    of request processing to handle duration field issues.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self._patched = False
        
    def __call__(self, request):
        # Apply the database operations patch only once
        if not self._patched:
            self._patch_all_connections()
            self._patched = True
        
        # Process the request
        return self.get_response(request)
    
    def _patch_all_connections(self):
        """
        Patch all database connections to handle duration field issues
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
                                
                        # Return a default duration of 0
                        return timedelta(0)
                
                # Apply the patch
                connection.ops.convert_durationfield_value = patched_convert_durationfield
                logger.info(f"Patched convert_durationfield_value for connection: {connection_name}")
