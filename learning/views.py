"""
Views for the learning app handling content delivery and progress tracking.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from courses.models import Course, Module
from .models import Content, Progress, Quiz


@login_required
def content_detail(request, content_id):
    """Display specific content and track student progress."""
    content = get_object_or_404(Content, id=content_id)
    course = content.module.course
    
    # Check if user is enrolled in the course
    if course not in request.user.profile.student_profile.enrolled_courses.all():
        messages.error(request, 'Please enroll in the course to access content.')
        return redirect('courses:detail', slug=course.slug)
    
    # Get or create progress record
    progress, created = Progress.objects.get_or_create(
        student=request.user,
        content=content,
        course=course
    )
    
    # Update last accessed time
    progress.last_accessed = timezone.now()
    progress.save()
    
    context = {
        'content': content,
        'progress': progress,
        'module': content.module,
        'course': course
    }
    
    # Add quiz context if content is a quiz
    if content.content_type == 'quiz':
        quiz = Quiz.objects.get(content=content)
        context['quiz'] = quiz
    
    return render(request, 'learning/content_detail.html', context)


@login_required
def mark_complete(request, content_id):
    """Mark content as completed."""
    content = get_object_or_404(Content, id=content_id)
    progress, created = Progress.objects.get_or_create(
        student=request.user,
        content=content,
        course=content.module.course
    )
    
    progress.completed = True
    progress.completion_date = timezone.now()
    progress.save()
    
    messages.success(request, 'Content marked as completed!')
    return redirect('learning:content_detail', content_id=content_id)


@login_required
def submit_quiz(request, quiz_id):
    """Handle quiz submission and scoring."""
    if request.method != 'POST':
        return redirect('home')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    content = quiz.content
    
    # Calculate score
    score = 0
    total_questions = 0
    # Quiz scoring logic here
    
    # Update progress
    progress, created = Progress.objects.get_or_create(
        student=request.user,
        content=content,
        course=content.module.course
    )
    
    progress.score = score
    progress.completed = True
    progress.completion_date = timezone.now()
    progress.save()
    
    messages.success(request, f'Quiz completed! Score: {score}%')
    return redirect('learning:content_detail', content_id=content.id)


@login_required
def manage_content(request, course_slug, module_id):
    """Manage content for a specific module."""
    if not request.user.profile.is_instructor:
        messages.error(request, 'Access denied. Instructor privileges required.')
        return redirect('home')
    
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    if request.user != course.instructor:
        messages.error(request, 'You do not have permission to manage this content.')
        return redirect('courses:detail', slug=course_slug)
    
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        title = request.POST.get('title')
        content_text = request.POST.get('content')
        order = request.POST.get('order')
        
        content = Content.objects.create(
            module=module,
            title=title,
            content_type=content_type,
            content=content_text,
            order=order
        )
        
        if request.FILES.get('file'):
            content.file = request.FILES['file']
            content.save()
        
        messages.success(request, 'Content added successfully.')
        return redirect('learning:manage_content', course_slug=course_slug, module_id=module_id)
    
    contents = module.learning_contents.all().order_by('order')
    return render(request, 'learning/manage_content.html', {
        'course': course,
        'module': module,
        'contents': contents
    })
