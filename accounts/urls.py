"""
URL patterns for the accounts app.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=views.CustomAuthenticationForm
    ), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect/', views.redirect_after_login, name='redirect_after_login'),
    
    # Dashboard URLs
    path('dashboard/', views.student_dashboard, name='dashboard'),
    path('instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    
    # Students management
    path('students/', views.student_list, name='student_list'),
    
    # Password management
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='password_change_done'), 
        name='password_change'
    ),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'),
        name='password_change_done'
    ),
    
    # Password reset
    path('password_reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt'
        ),
        name='password_reset'
    ),
    path('password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    path('reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
    
    # Profile management
    path('profile/', views.profile, name='profile'),
    path('enrolled-courses/', views.enrolled_courses, name='enrolled_courses'),
    path('course-progress/', views.course_progress, name='course_progress'),
    
    # Instructor routes
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('instructor/signup/', views.create_instructor, name='instructor_signup'),
    path('instructor/convert/', views.make_instructor, name='make_instructor'),
]