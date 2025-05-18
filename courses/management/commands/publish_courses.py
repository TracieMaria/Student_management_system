"""
Script to mark all courses as published and active
"""
from django.core.management.base import BaseCommand
from courses.models import Course

class Command(BaseCommand):
    help = 'Mark all courses as published and active'

    def handle(self, *args, **options):
        courses = Course.objects.all()
        count = courses.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No courses found in the database.'))
            return
        
        # Update all courses
        courses.update(is_published=True, is_active=True)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully published {count} courses!')
        )
