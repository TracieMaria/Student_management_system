"""
Views for the assignments functionality
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from courses.models import Course, Module
from learning.assignment_models import Assignment, AssignmentSubmission
from django.db.models import Q
from datetime import datetime


@login_required
def assignment_list(request):
    """Display all assignments for enrolled courses"""
    try:
        from django.db import connection
        import logging
        from datetime import timedelta
    
        if request.user.profile.is_instructor:
            # For instructors, show assignments for courses they teach
            courses = Course.objects.filter(instructor=request.user)
            
            # Use raw SQL to avoid DurationField conversion errors
            instructor_id = request.user.id
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT a.id
                    FROM learning_assignment a
                    JOIN courses_course c ON a.course_id = c.id
                    WHERE c.instructor_id = %s
                """, [instructor_id])
                
                assignment_ids = [row[0] for row in cursor.fetchall()]
            
            # Get assignments by ID to avoid timedelta issues
            assignments = []
            for assignment_id in assignment_ids:
                try:
                    assignment = Assignment.objects.get(id=assignment_id)
                    assignments.append(assignment)
                except Assignment.DoesNotExist:
                    continue
                    
        else:
            # For students, safely get enrolled courses
            student_profile = request.user.profile.student_profile
            enrolled_courses = student_profile.enrolled_courses.all()
            
            # Get assignment IDs using raw SQL
            course_ids = [course.id for course in enrolled_courses]
            if course_ids:
                with connection.cursor() as cursor:
                    placeholders = ','.join(['%s' for _ in course_ids])
                    cursor.execute(f"""
                        SELECT id
                        FROM learning_assignment
                        WHERE course_id IN ({placeholders})
                    """, course_ids)
                    
                    assignment_ids = [row[0] for row in cursor.fetchall()]
                
                # Get assignments by ID to avoid timedelta issues
                assignments = []
                for assignment_id in assignment_ids:
                    try:
                        assignment = Assignment.objects.get(id=assignment_id)
                        assignments.append(assignment)
                    except Assignment.DoesNotExist:
                        continue
                        
                # Add submission status to each assignment
                for assignment in assignments:
                    try:
                        submission = AssignmentSubmission.objects.get(
                            assignment=assignment,
                            student=request.user
                        )
                        assignment.submission_status = submission.status
                        assignment.submission_score = submission.score
                        assignment.submission = submission
                    except AssignmentSubmission.DoesNotExist:
                        assignment.submission_status = "Not Submitted"
                        assignment.submission_score = None
                        assignment.submission = None            
                    else:
                        assignment.submission_status = "Not Submitted"
                assignments = []
    except Exception as e:
        # Handle any exceptions
        logging.getLogger(__name__).error(f"Error in assignment_list: {str(e)}", exc_info=True)
        assignments = []
    
    # Pre-process assignments to add a flag for unique courses
    # This helps the template avoid using the problematic last_different filter
    processed_assignments = []
    course_ids = set()
    
    for assignment in assignments:
        # Add a flag to indicate if this is a new course
        assignment.is_new_course = assignment.course.id not in course_ids
        course_ids.add(assignment.course.id)
        processed_assignments.append(assignment)
      # Replace the assignments queryset with our processed list
    assignments = processed_assignments
    
    context = {
        'assignments': assignments,
        'is_instructor': request.user.profile.is_instructor,
        'now': timezone.now(),
    }
    
    # If user is an instructor, add their courses to the context for the course selection dropdown
    if request.user.profile.is_instructor:
        courses = Course.objects.filter(instructor=request.user)
        context['courses'] = courses
        
    return render(request, 'learning/assignment_list.html', context)


@login_required
def assignment_detail(request, assignment_id):
    """Display details of a specific assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check if user is instructor or enrolled student
    is_instructor = request.user.profile.is_instructor
    if not is_instructor:
        student_profile = request.user.profile.student_profile
        if assignment.course not in student_profile.enrolled_courses.all():
            messages.error(request, "You must be enrolled in this course to view assignments.")
            return redirect('courses:course_list')
    
    # Get or initialize submission if student
    submission = None
    if not is_instructor:
        try:
            submission = AssignmentSubmission.objects.get(
                assignment=assignment,
                student=request.user
            )
        except AssignmentSubmission.DoesNotExist:
            submission = None
    else:
        # For instructors, get all submissions
        submissions = assignment.submissions.all()
        context = {
            'assignment': assignment,
            'submissions': submissions,
            'is_instructor': True
        }
        return render(request, 'learning/assignment_detail.html', context)
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'is_instructor': is_instructor,
        'is_past_due': assignment.is_past_due
    }
    return render(request, 'learning/assignment_detail.html', context)


@login_required
def submit_assignment(request, assignment_id):
    """Handle student assignment submissions"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Verify student is enrolled in the course
    student_profile = request.user.profile.student_profile
    if assignment.course not in student_profile.enrolled_courses.all():
        messages.error(request, "You must be enrolled in this course to submit assignments.")
        return redirect('courses:course_list')
    
    # Check if assignment is past due
    is_late = timezone.now() > assignment.due_date
    
    if request.method == 'POST':
        content = request.POST.get('content', '')
        submission_file = request.FILES.get('submission_file', None)
        
        # Create or update submission
        submission, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment,
            student=request.user,
            defaults={
                'content': content,
                'status': 'submitted'
            }
        )
        
        if not created:
            submission.content = content
            submission.status = 'submitted'
            submission.submission_date = timezone.now()
        
        if submission_file:
            submission.file = submission_file
        
        submission.save()
        
        if is_late:
            messages.warning(request, "Your submission was recorded but it was submitted after the due date.")
        else:
            messages.success(request, "Assignment submitted successfully!")
        
        return redirect('learning:assignment_detail', assignment_id=assignment.id)
    
    # Check if already submitted
    try:
        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
            student=request.user
        )
        context = {
            'assignment': assignment,
            'submission': submission,
            'is_edit': True,
            'is_late': is_late
        }
    except AssignmentSubmission.DoesNotExist:
        context = {
            'assignment': assignment,
            'is_edit': False,
            'is_late': is_late
        }
    
    return render(request, 'learning/submit_assignment.html', context)


@login_required
def grade_submission(request, submission_id):
    """Allow instructors to grade student submissions"""
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    assignment = submission.assignment
    
    # Verify user is the course instructor
    if request.user != assignment.course.instructor:
        messages.error(request, "You must be the course instructor to grade submissions.")
        return redirect('courses:course_list')
    
    if request.method == 'POST':
        score = request.POST.get('score', '')
        feedback = request.POST.get('feedback', '')
        
        try:
            score = float(score)
            if score < 0 or score > assignment.total_points:
                raise ValueError
            
            submission.score = score
            submission.feedback = feedback
            submission.status = 'graded'
            submission.save()
            
            messages.success(request, "Submission graded successfully!")
            
            # Update student's grade for the course
            from learning.grade_models import Grade
            grade, _ = Grade.objects.get_or_create(
                student=submission.student,
                course=assignment.course
            )
            grade.calculate_grade()
            
        except ValueError:
            messages.error(request, f"Please enter a valid score between 0 and {assignment.total_points}.")
        
        return redirect('learning:assignment_detail', assignment_id=assignment.id)
    
    context = {
        'submission': submission,
        'assignment': assignment,
        'student': submission.student
    }
    return render(request, 'learning/grade_submission.html', context)


@login_required
def create_assignment(request, course_id):
    """Allow instructors to create new assignments"""
    course = get_object_or_404(Course, id=course_id)
    
    # Verify user is the course instructor
    if request.user != course.instructor:
        messages.error(request, "You must be the course instructor to create assignments.")
        return redirect('courses:course_list')
    
    if request.method == 'POST':
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        module_id = request.POST.get('module', None)
        due_date_str = request.POST.get('due_date', '')
        total_points = request.POST.get('total_points', 100)
        difficulty = request.POST.get('difficulty', 'intermediate')
        
        if not title or not description or not due_date_str:
            messages.error(request, "Please fill out all required fields.")
            return redirect('learning:create_assignment', course_id=course.id)
        
        try:
            # Parse the datetime string into a datetime object
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            
            module = None
            if module_id:
                module = get_object_or_404(Module, id=module_id, course=course)
            
            assignment = Assignment.objects.create(
                title=title,
                description=description,
                course=course,
                module=module,
                due_date=due_date,
                total_points=total_points,
                difficulty=difficulty
            )
            
            messages.success(request, f"Assignment '{title}' created successfully!")
            return redirect('learning:assignment_detail', assignment_id=assignment.id)
            
        except ValueError as e:
            messages.error(request, f"Invalid date format. Please use the date picker to select a date and time.")
        except Exception as e:
            messages.error(request, f"Error creating assignment: {str(e)}")
    
    context = {
        'course': course,
        'modules': course.modules.all()
    }
    return render(request, 'learning/create_assignment.html', context)
