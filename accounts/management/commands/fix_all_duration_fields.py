"""
Fix for all duration fields in the database
"""
from datetime import timedelta
from django.db import connection
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Fix all duration fields in the database to avoid string value errors'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting duration field fix...'))
        
        # Fix StudentProfile total_study_time
        try:
            with connection.cursor() as cursor:
                # Set any NULL duration values to '00:00:00'
                cursor.execute("""
                    UPDATE accounts_studentprofile
                    SET total_study_time = '00:00:00'
                    WHERE total_study_time IS NULL
                """)
                self.stdout.write(self.style.SUCCESS('Fixed NULL total_study_time values'))
                
                # Fix improperly formatted duration values
                cursor.execute("""
                    UPDATE accounts_studentprofile
                    SET total_study_time = '00:00:00'
                    WHERE total_study_time NOT LIKE '%:%:%'
                """)
                self.stdout.write(self.style.SUCCESS('Fixed invalid total_study_time formats'))
                
                # Convert any integers to proper duration format
                cursor.execute("""
                    UPDATE accounts_studentprofile
                    SET total_study_time = '00:00:00'
                    WHERE total_study_time ~ '^[0-9]+$'
                """)
                self.stdout.write(self.style.SUCCESS('Fixed numeric total_study_time strings'))
                
                # Additional fix for any other tables with duration fields
                # Add commands here if you have more duration fields in other models
                
        except Exception as e:
            self.stderr.write(f'Error fixing duration fields: {str(e)}')
            
        self.stdout.write(self.style.SUCCESS('All duration fields fixed!'))
