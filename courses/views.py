"""
Views for the courses app handling course management and display.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Course, Module, Category
from learning.models import Content
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView


def course_list(request):
    """Display list of all available courses."""
    courses = Course.objects.filter(is_active=True).annotate(
        student_count=Count('enrolled_students'),
        module_count=Count('modules')
    )
    return render(request, 'courses/course_list.html', {'courses': courses})


def course_detail(request, slug):
    """Display detailed information about a specific course."""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    modules = course.modules.all().prefetch_related('contents')
    
    enrolled = False
    if request.user.is_authenticated:
        enrolled = course in request.user.profile.student_profile.enrolled_courses.all()
    
    context = {
        'course': course,
        'modules': modules,
        'enrolled': enrolled,
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def enroll_course(request, slug):
    """Handle course enrollment for authenticated users with better error handling."""
    from django.db import connection
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Use raw SQL to get course data to avoid duration field issues
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title
                FROM courses_course
                WHERE slug = %s AND is_active = 1
            """, [slug])
            course_data = cursor.fetchone()
            
            if not course_data:
                messages.error(request, 'Course not found or not active.')
                return redirect('courses:course_list')
                
            course_id, course_title = course_data
    except Exception as e:
        logger.error(f"Error in enroll_course SQL query: {str(e)}")
        # Fallback to normal ORM with our patched duration handling
        course = get_object_or_404(Course, slug=slug, is_active=True)
        course_id = course.id
        course_title = course.title
    
    student_profile = request.user.profile.student_profile
    
    # Check if already enrolled
    is_enrolled = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM accounts_studentprofile_enrolled_courses
                WHERE studentprofile_id = %s AND course_id = %s
            """, [student_profile.id, course_id])
            is_enrolled = cursor.fetchone()[0] > 0
    except Exception as e:
        logger.error(f"Error checking enrollment: {str(e)}")
        # Fallback to ORM check
        course = Course.objects.get(id=course_id)
        is_enrolled = course in student_profile.enrolled_courses.all()
    
    if is_enrolled:
        messages.warning(request, 'You are already enrolled in this course.')
    else:
        try:
            # Use raw SQL to add enrollment
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO accounts_studentprofile_enrolled_courses
                    (studentprofile_id, course_id)
                    VALUES (%s, %s)
                """, [student_profile.id, course_id])
            messages.success(request, f'Successfully enrolled in {course_title}')
        except Exception as e:
            logger.error(f"Error enrolling: {str(e)}")
            # Fallback to ORM
            course = Course.objects.get(id=course_id)
            student_profile.enrolled_courses.add(course)
            messages.success(request, f'Successfully enrolled in {course_title}')
    
    return redirect('courses:course_detail', slug=slug)


@login_required
def instructor_course_list(request):
    """Display list of courses for an instructor."""
    if not request.user.profile.is_instructor:
        messages.error(request, 'Access denied. Instructor privileges required.')
        return redirect('home')
    
    courses = Course.objects.filter(instructor=request.user).annotate(
        student_count=Count('enrolled_students'),
        module_count=Count('modules')
    )
    return render(request, 'courses/instructor_course_list.html', {'courses': courses})


@login_required
def create_course(request):
    """Handle creation of new courses by instructors."""
    if not request.user.profile.is_instructor:
        messages.error(request, 'Access denied. Instructor privileges required.')
        return redirect('home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        thumbnail = request.FILES.get('thumbnail')
        duration_str = request.POST.get('duration')
        
        # Convert duration string to timedelta
        from datetime import timedelta
        import re
        
        # Default duration if parsing fails
        duration = timedelta(days=30)  # Default to 30 days
        
        if duration_str:
            # Try to parse the duration string
            try:
                # Check for weeks pattern (e.g. "6 weeks")
                weeks_match = re.search(r'(\d+)\s*weeks?', duration_str, re.IGNORECASE)
                if weeks_match:
                    duration = timedelta(weeks=int(weeks_match.group(1)))
                
                # Check for days pattern (e.g. "30 days")
                days_match = re.search(r'(\d+)\s*days?', duration_str, re.IGNORECASE)
                if days_match:
                    duration = timedelta(days=int(days_match.group(1)))
                
                # Check for hours pattern (e.g. "24 hours")
                hours_match = re.search(r'(\d+)\s*hours?', duration_str, re.IGNORECASE)
                if hours_match:
                    duration = timedelta(hours=int(hours_match.group(1)))
                    
                # If it's just a number, assume it's days
                if duration_str.strip().isdigit():
                    duration = timedelta(days=int(duration_str.strip()))
            except (ValueError, AttributeError):
                # If parsing fails, use the default duration
                pass
        
        course = Course.objects.create(
            instructor=request.user,
            title=title,
            description=description,
            thumbnail=thumbnail,
            duration=duration
        )
        messages.success(request, f'Course "{title}" created successfully.')
        return redirect('courses:instructor_course_list')
    
    return render(request, 'courses/create_course.html')


@login_required
def edit_course(request, slug):
    """Handle editing of existing courses by instructors."""
    course = get_object_or_404(Course, slug=slug)
    
    if request.user != course.instructor:
        messages.error(request, 'You do not have permission to edit this course.')
        return redirect('courses:course_detail', slug=slug)
    if request.method == 'POST':
        course.title = request.POST.get('title', course.title)
        course.description = request.POST.get('description', course.description)
        if 'thumbnail' in request.FILES:
            course.thumbnail = request.FILES['thumbnail']
        
        # Handle duration string conversion
        duration_str = request.POST.get('duration')
        if duration_str:
            from datetime import timedelta
            import re
            
            # Try to parse the duration string
            try:
                # Check for weeks pattern (e.g. "6 weeks")
                weeks_match = re.search(r'(\d+)\s*weeks?', duration_str, re.IGNORECASE)
                if weeks_match:
                    course.duration = timedelta(weeks=int(weeks_match.group(1)))
                
                # Check for days pattern (e.g. "30 days")
                days_match = re.search(r'(\d+)\s*days?', duration_str, re.IGNORECASE)
                if days_match:
                    course.duration = timedelta(days=int(days_match.group(1)))
                
                # Check for hours pattern (e.g. "24 hours")
                hours_match = re.search(r'(\d+)\s*hours?', duration_str, re.IGNORECASE)
                if hours_match:
                    course.duration = timedelta(hours=int(hours_match.group(1)))
                    
                # If it's just a number, assume it's days
                if duration_str.strip().isdigit():
                    course.duration = timedelta(days=int(duration_str.strip()))
            except (ValueError, AttributeError):
                # If parsing fails, don't update the duration
                pass
        
        course.is_active = request.POST.get('is_active', '') == 'on'
        course.save()
        messages.success(request, 'Course updated successfully.')
        return redirect('courses:course_detail', slug=course.slug)
    
    return render(request, 'courses/edit_course.html', {'course': course})


@login_required
def manage_modules(request, slug):
    """Handle module management for a course."""
    course = get_object_or_404(Course, slug=slug)
    if request.user != course.instructor:
        messages.error(request, 'You do not have permission to manage this course\'s modules.')
        return redirect('courses:course_detail', slug=slug)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        order = request.POST.get('order')
        
        Module.objects.create(
            course=course,
            title=title,
            description=description,
            order=order
        )
        messages.success(request, 'Module added successfully.')
        return redirect('courses:manage_modules', slug=slug)
    
    modules = course.modules.all().order_by('order')
    return render(request, 'courses/manage_modules.html', {
        'course': course,
        'modules': modules
    })


class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Course.objects.filter(is_active=True)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modules'] = self.object.modules.all()
        return context


@login_required
def course_content(request, course_slug, module_id):
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    contents = module.contents.all()
    
    return render(request, 'courses/course_content.html', {
        'course': course,
        'module': module,
        'contents': contents
    })
