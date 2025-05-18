"""
Models for the learning app managing content delivery and progress tracking.
"""
from django.db import models
from django.conf import settings
from courses.models import Module, Course
from .assignment_models import Assignment, AssignmentSubmission
from .grade_models import Grade


class Content(models.Model):
    """Content model representing different types of learning materials."""
    CONTENT_TYPES = (
        ('video', 'Video'),
        ('text', 'Text'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    )    
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE,
        related_name='learning_contents'
    )
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content = models.TextField()
    file = models.FileField(upload_to='content_files/', blank=True, null=True)
    url = models.URLField(blank=True)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['module', 'order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class Progress(models.Model):
    """
    Progress model for tracking student progress through course content.
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name='progress')
    course = models.ForeignKey(Course,
                             on_delete=models.CASCADE,
                             related_name='student_progress')
    content = models.ForeignKey(Content,
                              on_delete=models.CASCADE,
                              related_name='student_progress')
    completed = models.BooleanField(default=False)
    score = models.FloatField(null=True, blank=True)
    time_spent = models.DurationField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    completion_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['student', 'content']
        verbose_name_plural = 'Progress'

    def __str__(self):
        return f"{self.student.username}'s progress in {self.content.title}"


class Quiz(models.Model):
    """
    Quiz model for assessment content.
    """
    content = models.OneToOneField(Content,
                                 on_delete=models.CASCADE,
                                 related_name='quiz',
                                 limit_choices_to={'content_type': 'quiz'})
    passing_score = models.FloatField(default=70.0)
    time_limit = models.DurationField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Quizzes'

    def __str__(self):
        return f"Quiz for {self.content.title}"
