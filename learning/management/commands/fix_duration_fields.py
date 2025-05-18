"""
Management command to fix all duration fields in the database
"""
from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fixes all duration fields in the database to ensure proper format and prevent errors'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting comprehensive fix for all duration fields...'))
        
        # Fix Progress.time_spent fields
        try:
            with connection.cursor() as cursor:
                # Fix null values or invalid formats
                cursor.execute("""
                    UPDATE learning_progress
                    SET time_spent = '00:00:00'
                    WHERE time_spent IS NULL OR
                          time_spent NOT LIKE '__:__:__' OR
                          time_spent ~ '^[0-9]+$'
                """)
                self.stdout.write(f'Fixed Progress.time_spent values')
        except Exception as e:
            self.stderr.write(f'Error fixing Progress.time_spent: {str(e)}')
            logger.error(f'Error fixing Progress.time_spent: {str(e)}')
            
        # Fix Quiz.time_limit fields
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE learning_quiz
                    SET time_limit = '01:00:00'
                    WHERE time_limit IS NULL OR
                          time_limit NOT LIKE '__:__:__' OR
                          time_limit ~ '^[0-9]+$'
                """)
                self.stdout.write(f'Fixed Quiz.time_limit values')
        except Exception as e:
            self.stderr.write(f'Error fixing Quiz.time_limit: {str(e)}')
            logger.error(f'Error fixing Quiz.time_limit: {str(e)}')
            
        # Fix Course.duration fields
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE courses_course
                    SET duration = '00:00:00'
                    WHERE duration IS NULL OR
                          duration NOT LIKE '__:__:__' OR
                          duration ~ '^[0-9]+$'
                """)
                self.stdout.write(f'Fixed Course.duration values')
        except Exception as e:
            self.stderr.write(f'Error fixing Course.duration: {str(e)}')
            logger.error(f'Error fixing Course.duration: {str(e)}')
            
        # Fix StudentProfile total_study_time
        try:
            with connection.cursor() as cursor:
                # Check if the table and column exist
                cursor.execute("""
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'accounts_studentprofile'
                    AND column_name = 'total_study_time'
                """)
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE accounts_studentprofile
                        SET total_study_time = '00:00:00'
                        WHERE total_study_time IS NULL OR
                              total_study_time NOT LIKE '__:__:__' OR
                              total_study_time ~ '^[0-9]+$'
                    """)
                    self.stdout.write(f'Fixed StudentProfile.total_study_time values')
        except Exception as e:
            self.stderr.write(f'Error fixing StudentProfile.total_study_time: {str(e)}')
            logger.error(f'Error fixing StudentProfile.total_study_time: {str(e)}')
            
        self.stdout.write(self.style.SUCCESS('Successfully fixed all duration fields!'))
