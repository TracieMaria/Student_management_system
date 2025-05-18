from django.apps import AppConfig
from django.db import connections
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    
    def ready(self):
        """
        This method is called when Django starts. We use it to patch
        the database operations to handle duration field conversion properly.
        """
        # Patch all database connections to handle duration field issues
        self._patch_db_operations()
        
    def _patch_db_operations(self):
        """
        Monkey patch Django's database operations layer to safely handle duration fields
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
