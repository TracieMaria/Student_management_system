"""
URL configuration for elearning_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),    
    # App URLs
    path('accounts/', include('accounts.urls')),  # Your custom accounts URLs
    path('account/', include('allauth.urls')),  # Django-allauth URLs as fallback
    path('courses/', include('courses.urls')),
    path('learning/', include('learning.urls')),
    path('students/', include([
        path('', lambda request: redirect('accounts:student_list'), name='students_redirect'),
    ])),
    # Direct access shortcuts
    path('grades/', include([
        path('', lambda request: redirect('learning:grades_dashboard'), name='grades_redirect'),
    ])),
    path('assignments/', lambda request: redirect('learning:assignment_list'), name='assignments_redirect'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Add django-browser-reload URLs
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
