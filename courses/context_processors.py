"""
Context processors for the courses app.
"""
from .models import Course

def featured_courses(request):
    """
    Add featured courses to the context of all templates.
    Currently shows the 6 most recent active courses.
    """
    courses = Course.objects.filter(is_active=True).order_by('-created_at')[:6]
    return {
        'featured_courses': courses
    }