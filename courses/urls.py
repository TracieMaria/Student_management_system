"""
URL patterns for the courses app.
"""
from django.urls import path
from . import views
from .enrollment_views import (
    enrollment_management, course_enrollments, enroll_student, unenroll_student
)

app_name = 'courses'

urlpatterns = [
    # Course viewing and enrollment
    path('', views.CourseListView.as_view(), name='course_list'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('<slug:slug>/enroll/', views.enroll_course, name='enroll_course'),
    path('<slug:course_slug>/module/<int:module_id>/', views.course_content, name='course_content'),
    
    # Instructor routes
    path('instructor/courses/', views.instructor_course_list, name='instructor_course_list'),
    path('instructor/course/create/', views.create_course, name='create_course'),
    path('instructor/course/<slug:slug>/edit/', views.edit_course, name='edit_course'),
    path('instructor/course/<slug:slug>/modules/', views.manage_modules, name='manage_modules'),
    
    # Enrollment management
    path('enrollments/', enrollment_management, name='enrollment_management'),
    path('course/<int:course_id>/enrollments/', course_enrollments, name='course_enrollments'),
    path('course/<int:course_id>/enroll-student/', enroll_student, name='enroll_student'),
    path('course/<int:course_id>/unenroll-student/<int:student_id>/', unenroll_student, name='unenroll_student'),
]