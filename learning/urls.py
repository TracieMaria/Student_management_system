"""
URL patterns for the learning app.
"""
from django.urls import path
from . import views
from .assignment_views import (
    assignment_list, assignment_detail, submit_assignment, grade_submission, create_assignment
)
from .grade_views import (
    grades_dashboard, course_grades, update_course_grade, recalculate_grades
)

app_name = 'learning'

urlpatterns = [
    # Content viewing and progress
    path('content/<int:content_id>/', views.content_detail, name='content_detail'),
    path('content/<int:content_id>/complete/', views.mark_complete, name='mark_complete'),
    
    # Quiz handling
    path('quiz/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    
    # Content management
    path('course/<slug:course_slug>/module/<int:module_id>/content/',
         views.manage_content, name='manage_content'),
         
    # Assignment routes
    path('assignments/', assignment_list, name='assignment_list'),
    path('assignments/<int:assignment_id>/', assignment_detail, name='assignment_detail'),
    path('assignments/<int:assignment_id>/submit/', submit_assignment, name='submit_assignment'),
    path('submissions/<int:submission_id>/grade/', grade_submission, name='grade_submission'),
    path('course/<int:course_id>/assignments/create/', create_assignment, name='create_assignment'),
    
    # Grade routes
    path('grades/', grades_dashboard, name='grades_dashboard'),
    path('course/<int:course_id>/grades/', course_grades, name='course_grades'),
    path('course/<int:course_id>/student/<int:student_id>/grade/', update_course_grade, name='update_course_grade'),
    path('course/<int:course_id>/recalculate-grades/', recalculate_grades, name='recalculate_grades'),
]