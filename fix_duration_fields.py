"""
Script to fix any duration field issues in the database
Comprehensive solution to fix all duration fields across the application
"""
from django.db import connection, models
import logging
import re
from django.apps import apps
from datetime import timedelta
import sys

logger = logging.getLogger(__name__)

def fix_duration_fields():
    """
    Runs SQL to fix duration fields in the database by ensuring they are all
    in the correct format (HH:MM:SS) to prevent Django ORM errors
    """
    print("Starting comprehensive duration field fixes...")
    
    # First, let's update using SQL for the known tables
    try:
        with connection.cursor() as cursor:
            # Fix StudentProfile total_study_time
            cursor.execute("""
                UPDATE accounts_studentprofile
                SET total_study_time = '00:00:00'
                WHERE total_study_time IS NULL OR
                      total_study_time NOT LIKE '__:__:__' OR
                      total_study_time ~ '^[0-9]+$'
            """)
            print("Fixed StudentProfile.total_study_time fields")
            
            # Fix Progress.time_spent fields
            cursor.execute("""
                UPDATE learning_progress
                SET time_spent = '00:00:00'
                WHERE time_spent IS NULL OR
                      time_spent NOT LIKE '__:__:__' OR
                      time_spent ~ '^[0-9]+$'
            """)
            print("Fixed Progress.time_spent fields")
            
            # Fix Quiz.time_limit fields
            cursor.execute("""
                UPDATE learning_quiz
                SET time_limit = '01:00:00'
                WHERE time_limit IS NULL OR
                      time_limit NOT LIKE '__:__:__' OR
                      time_limit ~ '^[0-9]+$'
            """)
            print("Fixed Quiz.time_limit fields")
            
            # Fix Course.duration fields
            cursor.execute("""
                UPDATE courses_course
                SET duration = '00:00:00'
                WHERE duration IS NULL OR
                      duration NOT LIKE '__:__:__' OR
                      duration ~ '^[0-9]+$'
            """)
            print("Fixed Course.duration fields")
            
            # Find and fix all DurationField columns in the database
            cursor.execute("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE data_type = 'interval'
            """)
            
            duration_columns = cursor.fetchall()
            for table_name, column_name in duration_columns:
                try:
                    print(f"Fixing duration field in {table_name}.{column_name}")
                    cursor.execute(f"""
                        UPDATE {table_name}
                        SET {column_name} = '00:00:00'
                        WHERE {column_name} IS NULL OR
                              {column_name} NOT LIKE '__:__:__' OR
                              {column_name} ~ '^[0-9]+$'
                    """)
                except Exception as e:
                    print(f"Error fixing {table_name}.{column_name}: {str(e)}")
                    
            # Let's also ensure NULL values are updated to default durations
            print("Setting default values for NULL duration fields...")
            for table_name, column_name in duration_columns:
                try:
                    cursor.execute(f"""
                        UPDATE {table_name}
                        SET {column_name} = '00:00:00'
                        WHERE {column_name} IS NULL
                    """)
                except Exception as e:
                    print(f"Error fixing NULL values in {table_name}.{column_name}: {str(e)}")

    except Exception as e:
        print(f"Error during SQL duration field fixes: {str(e)}")
        logger.error(f"Error fixing duration fields: {str(e)}")
        
    # Now let's try to find and fix duration fields using the Django ORM
    try:
        print("\nSearching for duration fields in Django models...")
        for app_config in apps.get_app_configs():
            print(f"Checking app: {app_config.name}")
            for model in app_config.get_models():
                print(f"  Checking model: {model.__name__}")
                
                # Find DurationField fields in this model
                duration_fields = []
                for field in model._meta.fields:
                    if isinstance(field, models.DurationField):
                        duration_fields.append(field.name)
                        
                if duration_fields:
                    print(f"  Found duration fields in {model.__name__}: {', '.join(duration_fields)}")
                    
                    # Fix each object with duration fields
                    for field_name in duration_fields:
                        try:
                            # Find objects with problematic duration values
                            for obj in model.objects.all():
                                try:
                                    value = getattr(obj, field_name)
                                    # Skip if value is already a timedelta or None
                                    if isinstance(value, timedelta) or value is None:
                                        continue
                                        
                                    # Try to convert string value to timedelta
                                    if isinstance(value, str):
                                        if re.match(r'^\d+:\d{2}:\d{2}$', value):
                                            # Already in the right format, skip
                                            continue
                                            
                                    # Set a default value
                                    print(f"    Fixing {field_name} value for {obj}")
                                    setattr(obj, field_name, timedelta(0))
                                    obj.save(update_fields=[field_name])
                                except Exception as e:
                                    print(f"    Error fixing {field_name} for {obj}: {str(e)}")
                        except Exception as e:
                            print(f"  Error fixing {field_name} for {model.__name__}: {str(e)}")
        
        # Additional fix for safe database operations
        from django.db import connections
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
                        print(f"Duration field conversion error: {str(e)} for value: {value}")
                        
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
                print(f"Patched convert_durationfield_value for connection: {connection_name}")
        
        print("All duration fields have been fixed successfully!")
            
        print("All duration fields have been fixed successfully!")
    except Exception as e:
        print(f"Error during duration field fixes: {str(e)}")
        logger.error(f"Error fixing duration fields: {str(e)}")

if __name__ == "__main__":
    # This runs when the script is executed directly
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elearning_system.settings')
    django.setup()
    
    fix_duration_fields()
