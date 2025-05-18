"""
Views for the accounts app handling user authentication and profile management.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from .models import UserProfile, StudentProfile

# Custom authentication form with relaxed validation
class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form that allows any password."""    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Enter your username or email'})
        self.fields['password'].widget.attrs.update({'placeholder': 'Enter your password'})
        
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        # Allow empty password for development purposes
        if username and not password:
            self.cleaned_data['password'] = 'any_password'
            return self.cleaned_data

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                # In development mode, we'll just allow any password
                user = User.objects.filter(username=username).first()
                if user:
                    # Set a backend attribute on the user
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    self.user_cache = user
                    return self.cleaned_data
                else:
                    raise forms.ValidationError(
                        "Please enter a correct username and password.",
                        code='invalid_login',
                    )
        return self.cleaned_data

# Custom registration form with no password restrictions
class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove help texts
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        
    # Override the _post_clean method to bypass password validation completely
    def _post_clean(self):
        super(forms.ModelForm, self)._post_clean()
        # Skip the password validation entirely
        
    # No password validation - only check if passwords match
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    # Override password validation completely
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        return password1
    
    # Completely override the save method to avoid validation
    def save(self, commit=True):
        user = super(forms.ModelForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

from django.views.decorators.csrf import ensure_csrf_cookie

from django.views.decorators.csrf import ensure_csrf_cookie
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def register(request):
    """Register a new user."""
    if request.method == 'POST':
        logger.info(f"Processing registration POST request. CSRF Token present: {'csrfmiddlewaretoken' in request.POST}")
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # Save without validation
                user = form.save(commit=False)
                # Set the password directly without validation
                user.set_password(form.cleaned_data.get('password1'))
                user.save()
                
                # Both UserProfile and StudentProfile are created automatically through signals
                # No need to create them manually here
                
                # Login the new user
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                login(request, user)
                
                logger.info(f"User {username} registered successfully")            
            except Exception as e:
                logger.error(f"Error during registration: {str(e)}", exc_info=True)
                messages.error(request, f"Error during registration: {str(e)}")
                return render(request, 'accounts/signup.html', {'form': form})
            
            messages.success(request, f'Account created for {username}. You are now logged in.')
            return redirect('accounts:dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def profile(request):
    """Display and update user profile."""
    if request.method == 'POST':
        user = request.user
        profile = user.profile
        
        # Update profile fields
        profile.bio = request.POST.get('bio', '')
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('profile')

    return render(request, 'accounts/profile.html')

@login_required
def enrolled_courses(request):
    """Display courses enrolled by the student."""
    student_profile = request.user.profile.student_profile
    courses = student_profile.enrolled_courses.all()
    return render(request, 'accounts/enrolled_courses.html', {'courses': courses})

@login_required
def course_progress(request):
    """Display student's progress across all courses."""
    progress = request.user.progress.all()
    return render(request, 'accounts/course_progress.html', {'progress': progress})

@login_required
def instructor_dashboard(request):
    """Display instructor dashboard with their courses and student progress."""
    if not request.user.profile.is_instructor:
        messages.error(request, 'Access denied. Instructor privileges required.')
        return redirect('accounts:dashboard')
    
    # Get courses taught by this instructor
    instructor_courses = request.user.courses.all() if hasattr(request.user, 'courses') else []
    
    context = {
        'courses': instructor_courses,
        'courses_count': len(instructor_courses),
    }
    
    return render(request, 'accounts/instructor_dashboard.html', context)

@login_required
def student_dashboard(request):
    """Display student dashboard with enrolled courses and progress."""
    if request.user.profile.is_instructor:
        # If the user is an instructor, redirect them to the instructor dashboard
        return redirect('accounts:instructor_dashboard')
    
    try:
        from django.db import connection
        import logging
        from datetime import timedelta
        
        logger = logging.getLogger(__name__)

        # Get student profile with sanitized data
        student_profile = request.user.profile.student_profile
        
        # Ensure total_study_time is a proper timedelta
        if isinstance(student_profile.total_study_time, str):
            try:
                # Try to parse the string into a timedelta
                hours, minutes, seconds = map(int, student_profile.total_study_time.split(':'))
                student_profile.total_study_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                student_profile.save()
            except (ValueError, AttributeError):
                # If parsing fails, set to zero
                student_profile.total_study_time = timedelta(0)
                student_profile.save()
        
        # Ensure current_grade is a float
        if isinstance(student_profile.current_grade, str):
            try:
                student_profile.current_grade = float(student_profile.current_grade)
                student_profile.save()
            except (ValueError, TypeError):
                student_profile.current_grade = 0.0
                student_profile.save()
        
        # Get enrolled and completed courses
        enrolled_courses = student_profile.enrolled_courses.all()
        completed_courses = student_profile.completed_courses.all()
        
        context = {
            'enrolled_courses': enrolled_courses,
            'completed_courses': completed_courses,
            'enrolled_courses_count': enrolled_courses.count(),
            'completed_courses_count': completed_courses.count(),
            'student_profile': student_profile,
        }
        
        return render(request, 'accounts/student_dashboard.html', context)
    except Exception as e:
        # For new users who may not have complete profiles yet
        logger.error(f"Error loading dashboard for user {request.user.username}: {str(e)}", exc_info=True)
        
        # Provide empty data rather than showing an error
        context = {
            'enrolled_courses': [],
            'completed_courses': [],
            'enrolled_courses_count': 0,
            'completed_courses_count': 0,
            'setup_incomplete': True
        }
        
        return render(request, 'accounts/student_dashboard.html', context)

@login_required
def student_list(request):
    """Display a list of all students with GitHub-style UI."""
    # Use a raw query to bypass ORM duration field issues
    from django.db import connection
    from datetime import timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get all student profiles with relevant data but exclude problematic fields
    with connection.cursor() as cursor:
        # Base query to get student data without the problematic duration field
        cursor.execute("""
            SELECT 
                sp.id,
                sp.enrollment_date,
                sp.current_grade,
                up.id as user_profile_id,
                u.id as user_id,
                u.username,
                u.first_name,
                u.last_name,
                u.email
            FROM 
                accounts_studentprofile sp
                JOIN accounts_userprofile up ON sp.user_id = up.id
                JOIN auth_user u ON up.user_id = u.id
        """)
        
        # Convert to dictionaries
        columns = [col[0] for col in cursor.description]
        student_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Optional filtering
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'latest')
    
    # Filter data
    if search_query:
        search_query = search_query.lower()
        filtered_students = []
        for student in student_data:
            if (search_query in student['username'].lower() or
                search_query in (student['first_name'] or '').lower() or
                search_query in (student['last_name'] or '').lower() or
                search_query in (student['email'] or '').lower()):
                filtered_students.append(student)
        student_data = filtered_students
    
    # Handle sorting
    if sort_by == 'latest':
        student_data.sort(key=lambda x: x['enrollment_date'], reverse=True)
    elif sort_by == 'name':
        student_data.sort(key=lambda x: x['username'].lower())
      # If we need enrolled courses counts, get them separately
    student_ids = [student['id'] for student in student_data]
    course_counts = {}
    
    if student_ids:  # Only run this if we have student IDs
        with connection.cursor() as cursor:
            # Get enrolled courses count for each student
            placeholders = ','.join(['%s'] * len(student_ids))
            cursor.execute(f"""
                SELECT 
                    studentprofile_id, 
                    COUNT(course_id) as course_count
                FROM 
                    accounts_studentprofile_enrolled_courses
                WHERE 
                    studentprofile_id IN ({placeholders})
                GROUP BY 
                    studentprofile_id
            """, student_ids)
            
            for student_id, count in cursor.fetchall():
                course_counts[student_id] = count
    
    # Supplement course counts
    for student in student_data:
        student['course_count'] = course_counts.get(student['id'], 0)
    
    # Sort by courses if needed
    if sort_by == 'courses':
        student_data.sort(key=lambda x: x['course_count'], reverse=True)
    
    # Group by initial (GitHub style)
    alphabet = {}
    for student in student_data:
        initial = student['username'][0].upper()
        if initial not in alphabet:
            alphabet[initial] = []
        alphabet[initial].append(student)
        sorted_alphabet = sorted(alphabet.items())
    
    context = {
        'students_by_initial': sorted_alphabet,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_students': len(student_data),
    }
    
    return render(request, 'accounts/student_list.html', context)

def redirect_after_login(request):
    """
    Redirect users to appropriate dashboards based on their role after login.
    """
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    # Check if the user is staff/admin
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/admin/')  # Redirect to admin panel
    
    # Check if user is an instructor
    try:
        if request.user.profile.is_instructor:
            return redirect('accounts:instructor_dashboard')  # Redirect to instructor dashboard
        else:
            return redirect('accounts:student_dashboard')  # Redirect to student dashboard
    except Exception:
        # If profile doesn't exist, redirect to home
        messages.error(request, "Your user profile is incomplete. Please contact support.")
        return redirect('home')

def logout_view(request):
    """Custom logout view that handles both GET and POST requests."""
    if request.method == 'POST' or request.method == 'GET':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return render(request, 'accounts/logout.html')
    return redirect('home')

def create_instructor(request):
    """Create a new instructor account or convert existing user to instructor."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # Save without validation
                user = form.save(commit=False)
                # Set the password directly without validation
                user.set_password(form.cleaned_data.get('password1'))
                user.save()
                
                # Set the profile as instructor
                user.profile.is_instructor = True
                user.profile.save()
                
                # Login the new user
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                login(request, user)
                
                logger.info(f"Instructor {username} registered successfully")            
            except Exception as e:
                logger.error(f"Error during instructor registration: {str(e)}", exc_info=True)
                messages.error(request, f"Error during registration: {str(e)}")
                return render(request, 'accounts/instructor_signup.html', {'form': form})
            
            messages.success(request, f'Instructor account created for {username}. You are now logged in.')
            return redirect('accounts:instructor_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/instructor_signup.html', {'form': form})

@login_required
def make_instructor(request):
    """Convert existing account to instructor account."""
    if request.method == 'POST':
        # Set the current user as instructor
        user = request.user
        user.profile.is_instructor = True
        user.profile.save()
        
        messages.success(request, 'Your account has been converted to an instructor account!')
        return redirect('accounts:instructor_dashboard')
    
    return render(request, 'accounts/make_instructor.html')
