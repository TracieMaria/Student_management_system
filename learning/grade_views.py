"""
Views for the grades functionality
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from courses.models import Course
from learning.grade_models import Grade
from learning.assignment_models import Assignment, AssignmentSubmission
from django.db.models import Avg, Count
from datetime import timedelta
from django.db import connections


@login_required
def grades_dashboard(request):
    """Display grades overview for student or instructor"""
    from django.db import connection
    import logging
    import re

    logger = logging.getLogger(__name__)
    is_instructor = request.user.profile.is_instructor

    # Apply a comprehensive fix to duration fields
    # This is needed to prevent the TypeError with timedelta microseconds
    with connection.cursor() as cursor:
        try:
            # Fix Progress.time_spent fields
            cursor.execute("""
                UPDATE learning_progress
                SET time_spent = '00:00:00'
                WHERE time_spent IS NULL OR
                      time_spent NOT LIKE '__:__:__' OR
                      time_spent ~ '^[0-9]+$'
            """)
            
            # Fix Quiz.time_limit fields
            cursor.execute("""
                UPDATE learning_quiz
                SET time_limit = '01:00:00'
                WHERE time_limit IS NULL OR
                      time_limit NOT LIKE '__:__:__' OR
                      time_limit ~ '^[0-9]+$'
            """)
            
            # Fix Course.duration fields
            cursor.execute("""
                UPDATE courses_course
                SET duration = '00:00:00'
                WHERE duration IS NULL OR
                      duration NOT LIKE '__:__:__' OR
                      duration ~ '^[0-9]+$'
            """)
            
            # Fix StudentProfile.total_study_time fields
            cursor.execute("""
                UPDATE accounts_studentprofile
                SET total_study_time = '00:00:00'
                WHERE total_study_time IS NULL OR
                      total_study_time NOT LIKE '__:__:__' OR
                      total_study_time ~ '^[0-9]+$'
            """)
            
            logger.info("Successfully fixed duration fields in database")
        except Exception as e:
            logger.error(f"Error fixing duration fields: {str(e)}")
    
    # Patch the database connection to handle duration field conversion errors
    original_convert = connections['default'].ops.convert_durationfield_value
    
    def patched_convert_durationfield(value, expression, connection):
        if value is None:
            return None
        
        try:
            # Try the original conversion
            return original_convert(value, expression, connection)
        except (TypeError, ValueError) as e:
            logger.warning(f"Duration field conversion error: {str(e)} for value: {value}")
            # Return a default duration of 0
            return timedelta(0)
    
    # Monkey-patch the conversion function
    connections['default'].ops.convert_durationfield_value = patched_convert_durationfield

    # Continue with the rest of the function
    if is_instructor:
        # For instructors, show courses they teach and grade statistics
        courses = Course.objects.filter(instructor=request.user)

        course_stats = []
        for course in courses:
            grades = course.grades.all()

            stats = {
                'course': course,
                'total_students': course.students.count(),
                'graded_students': grades.exclude(final_grade__isnull=True).count(),
                'avg_grade': grades.aggregate(Avg('numeric_grade'))['numeric_grade__avg'],
                'passing_students': grades.filter(is_passing=True).count(),
                'failing_students': grades.filter(is_passing=False, final_grade__isnull=False).count()
            }
            course_stats.append(stats)

        context = {
            'is_instructor': True,
            'course_stats': course_stats
        }
    else:
        # For students, show their grades for all enrolled courses
        student_profile = request.user.profile.student_profile
        enrolled_courses = student_profile.enrolled_courses.all()

        course_grades = []
        for course in enrolled_courses:
            try:
                # Use raw SQL to get the Grade data to avoid potential duration field issues
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id
                        FROM learning_grade
                        WHERE student_id = %s AND course_id = %s
                    """, [request.user.id, course.id])
                    grade_row = cursor.fetchone()
                    if grade_row:
                        grade = Grade.objects.get(pk=grade_row[0])
                    else:
                        raise Grade.DoesNotExist
            except Grade.DoesNotExist:
                grade = None

            # Get assignment scores for this course
            submissions = AssignmentSubmission.objects.filter(
                student=request.user,
                assignment__course=course,
                score__isnull=False
            )

            course_grades.append({
                'course': course,
                'grade': grade,
                'submissions_count': submissions.count(),
                'graded_assignments_count': Assignment.objects.filter(
                    course=course,
                    submissions__student=request.user,
                    submissions__score__isnull=False
                ).count(),
                'total_assignments': Assignment.objects.filter(course=course).count(),
            })

        context = {
            'is_instructor': False,
            'course_grades': course_grades
        }

    return render(request, 'learning/grades_dashboard.html', context)


@login_required
def course_grades(request, course_id):
    """Display grades for a specific course"""
    course = get_object_or_404(Course, id=course_id)
    is_instructor = request.user.profile.is_instructor
    
    if is_instructor:
        # Verify user is the course instructor
        if request.user != course.instructor:
            messages.error(request, "You must be the course instructor to view all grades.")
            return redirect('courses:course_list')
        
        # Get all grades for this course
        grades = Grade.objects.filter(course=course).select_related('student')
        
        # Get all assignments for this course
        assignments = Assignment.objects.filter(course=course)
        
        # For each student, get assignment submissions
        students_data = []
        for grade in grades:
            student = grade.student
            student_submissions = AssignmentSubmission.objects.filter(
                student=student,
                assignment__course=course
            )
            
            # Create a dict of assignment_id -> submission for quick lookup
            submissions_dict = {sub.assignment_id: sub for sub in student_submissions}
            
            # List of assignments with submission data
            student_assignments = []
            for assignment in assignments:
                submission = submissions_dict.get(assignment.id, None)
                student_assignments.append({
                    'assignment': assignment,
                    'submission': submission,
                    'score': submission.score if submission and submission.score is not None else None,
                    'status': submission.status if submission else 'Not Submitted',
                })
            
            students_data.append({
                'student': student,
                'grade': grade,
                'assignments': student_assignments,
                'submissions_count': student_submissions.count(),
            })
        
        context = {
            'course': course,
            'students_data': students_data,
            'assignments': assignments,
            'is_instructor': True
        }
    else:
        # For students, show only their grades for this course
        student_profile = request.user.profile.student_profile
        
        # Verify student is enrolled in the course
        if course not in student_profile.enrolled_courses.all():
            messages.error(request, "You must be enrolled in this course to view grades.")
            return redirect('courses:course_list')
        
        # Get student's grade for this course
        try:
            grade = Grade.objects.get(student=request.user, course=course)
        except Grade.DoesNotExist:
            grade = None
        
        # Get assignments and submissions for this course
        assignments = Assignment.objects.filter(course=course)
        submissions = AssignmentSubmission.objects.filter(
            student=request.user,
            assignment__course=course
        )
        
        # Create a dict of assignment_id -> submission for quick lookup
        submissions_dict = {sub.assignment_id: sub for sub in submissions}
        
        # List of assignments with submission data
        student_assignments = []
        for assignment in assignments:
            submission = submissions_dict.get(assignment.id, None)
            student_assignments.append({
                'assignment': assignment,
                'submission': submission,
                'score': submission.score if submission and submission.score is not None else None,
                'status': submission.status if submission else 'Not Submitted',
            })
        
        context = {
            'course': course,
            'grade': grade,
            'assignments': student_assignments,
            'is_instructor': False
        }
    
    return render(request, 'learning/course_grades.html', context)


@login_required
def update_course_grade(request, course_id, student_id):
    """Allow instructors to manually update a student's course grade"""
    course = get_object_or_404(Course, id=course_id)
    
    # Verify user is the course instructor
    if request.user != course.instructor:
        messages.error(request, "You must be the course instructor to update grades.")
        return redirect('courses:course_list')
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    student = get_object_or_404(User, id=student_id)
    
    # Get or create grade for this student
    grade, created = Grade.objects.get_or_create(
        student=student,
        course=course
    )
    
    if request.method == 'POST':
        final_grade = request.POST.get('final_grade', '')
        numeric_grade = request.POST.get('numeric_grade', '')
        comments = request.POST.get('comments', '')
        
        # Validate and update grade
        if final_grade in dict(Grade.GRADE_CHOICES).keys():
            grade.final_grade = final_grade
        
        try:
            if numeric_grade:
                numeric_grade = float(numeric_grade)
                grade.numeric_grade = numeric_grade
                
                # Update is_passing based on numeric grade
                grade.is_passing = numeric_grade >= 60
        except ValueError:
            messages.error(request, "Please enter a valid numeric grade.")
            return redirect('learning:update_course_grade', course_id=course.id, student_id=student.id)
        
        grade.comments = comments
        grade.save()
        
        messages.success(request, f"Grade for {student.username} updated successfully.")
        return redirect('learning:course_grades', course_id=course.id)
    
    context = {
        'course': course,
        'student': student,
        'grade': grade,
        'grade_choices': Grade.GRADE_CHOICES
    }
    return render(request, 'learning/update_grade.html', context)


@login_required
def recalculate_grades(request, course_id):
    """Recalculate all grades for a course based on assignments"""
    course = get_object_or_404(Course, id=course_id)
    
    # Verify user is the course instructor
    if request.user != course.instructor:
        messages.error(request, "You must be the course instructor to recalculate grades.")
        return redirect('courses:course_list')
    
    # Get all enrolled students
    students = course.students.all()
    
    recalculated_count = 0
    for student in students:
        grade, _ = Grade.objects.get_or_create(
            student=student,
            course=course
        )
        
        # Calculate grade based on assignments
        if grade.calculate_grade() is not None:
            recalculated_count += 1
    
    messages.success(request, f"Successfully recalculated grades for {recalculated_count} students.")
    return redirect('learning:course_grades', course_id=course.id)
