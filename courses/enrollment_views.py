"""
Views for enrollment management
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from courses.models import Course
from accounts.models import StudentProfile
from django.contrib.auth.models import User


@login_required
def enrollment_management(request):
    """Display enrollment management dashboard"""
    is_instructor = request.user.profile.is_instructor
    
    if is_instructor:
        # Show courses taught by instructor and students enrolled
        courses = Course.objects.filter(instructor=request.user)
        
        course_enrollments = []
        for course in courses:
            enrolled_students = course.enrolled_students.all()
            course_enrollments.append({
                'course': course,
                'student_count': enrolled_students.count(),
                'students': enrolled_students
            })
        
        context = {
            'is_instructor': True,
            'course_enrollments': course_enrollments
        }
    else:
        # Show courses student is enrolled in
        student_profile = request.user.profile.student_profile
        enrolled_courses = student_profile.enrolled_courses.all()
        available_courses = Course.objects.filter(is_published=True, is_active=True).exclude(id__in=enrolled_courses.values_list('id', flat=True))
        
        context = {
            'is_instructor': False,
            'enrolled_courses': enrolled_courses,
            'available_courses': available_courses
        }
    
    return render(request, 'courses/enrollment_management.html', context)


@login_required
def course_enrollments(request, course_id):
    """Display and manage enrollments for a specific course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Verify user is the course instructor
    if request.user != course.instructor:
        messages.error(request, "You must be the course instructor to manage enrollments.")
        return redirect('courses:course_list')
    
    enrolled_students = course.enrolled_students.all()
    
    context = {
        'course': course,
        'enrolled_students': enrolled_students,
        'student_count': enrolled_students.count()
    }
    return render(request, 'courses/course_enrollments.html', context)


@login_required
def enroll_student(request, course_id):
    """Allow instructors to manually enroll students"""
    course = get_object_or_404(Course, id=course_id)
    
    # Verify user is the course instructor
    if request.user != course.instructor:
        messages.error(request, "You must be the course instructor to manage enrollments.")
        return redirect('courses:course_list')
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        
        try:
            user = User.objects.get(username=username)
            student_profile = user.profile.student_profile
            
            if course in student_profile.enrolled_courses.all():
                messages.warning(request, f"{username} is already enrolled in this course.")
            else:
                student_profile.enrolled_courses.add(course)
                messages.success(request, f"Successfully enrolled {username} in {course.title}.")
        except User.DoesNotExist:
            messages.error(request, f"User {username} not found.")
        except AttributeError:
            messages.error(request, f"User {username} does not have a student profile.")
        
        return redirect('courses:course_enrollments', course_id=course.id)
    
    # Get all users with student profiles who are not enrolled
    enrolled_user_ids = course.enrolled_students.values_list('user__user_id', flat=True)
    available_students = StudentProfile.objects.exclude(user__user_id__in=enrolled_user_ids)
    
    context = {
        'course': course,
        'available_students': available_students
    }
    return render(request, 'courses/enroll_student.html', context)


@login_required
def unenroll_student(request, course_id, student_id):
    """Allow instructors to unenroll students"""
    course = get_object_or_404(Course, id=course_id)
    
    # Verify user is the course instructor
    if request.user != course.instructor:
        messages.error(request, "You must be the course instructor to manage enrollments.")
        return redirect('courses:course_list')
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    student = get_object_or_404(User, id=student_id)
    
    try:
        student_profile = student.profile.student_profile
        
        if course in student_profile.enrolled_courses.all():
            student_profile.enrolled_courses.remove(course)
            messages.success(request, f"Successfully unenrolled {student.username} from {course.title}.")
        else:
            messages.warning(request, f"{student.username} is not enrolled in this course.")
    except AttributeError:
        messages.error(request, f"User {student.username} does not have a student profile.")
    
    return redirect('courses:course_enrollments', course_id=course.id)
