from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix duration fields in the database to prevent string conversion errors'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to fix duration fields...')
        
        # Fix StudentProfile total_study_time
        try:
            with connection.cursor() as cursor:
                # Set any NULL duration values to '00:00:00'
                cursor.execute("""
                    UPDATE accounts_studentprofile
                    SET total_study_time = '00:00:00'
                    WHERE total_study_time IS NULL
                """)
                self.stdout.write('Fixed NULL total_study_time values')
                
                # Fix improperly formatted duration values
                cursor.execute("""
                    UPDATE accounts_studentprofile
                    SET total_study_time = '00:00:00'
                    WHERE total_study_time NOT LIKE '%:%:%'
                """)
                self.stdout.write('Fixed invalid total_study_time formats')
        except Exception as e:
            self.stderr.write(f'Error fixing duration fields: {str(e)}')
            logger.error(f'Error fixing duration fields: {str(e)}', exc_info=True)
            
        self.stdout.write(self.style.SUCCESS('Duration field fixes completed!'))
