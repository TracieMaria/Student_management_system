"""
Models for assignments management
"""
from django.db import models
from django.conf import settings
from courses.models import Course, Module
from django.utils import timezone


class Assignment(models.Model):
    """
    Assignment model representing course assignments for students to complete
    """
    DIFFICULTY_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, related_name='assignments', on_delete=models.CASCADE)
    module = models.ForeignKey(Module, related_name='assignments', on_delete=models.CASCADE, null=True, blank=True)
    due_date = models.DateTimeField()
    total_points = models.PositiveIntegerField(default=100)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date']
    
    def __str__(self):
        return self.title
    
    @property
    def is_past_due(self):
        return timezone.now() > self.due_date
    
    @property
    def time_remaining(self):
        if self.is_past_due:
            return None
        return self.due_date - timezone.now()


class AssignmentSubmission(models.Model):
    """
    Model for student assignment submissions
    """
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned for revision'),
    )
    
    assignment = models.ForeignKey(Assignment, related_name='submissions', on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='submissions', on_delete=models.CASCADE)
    submission_date = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    file = models.FileField(upload_to='assignment_submissions/', blank=True, null=True)
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    
    class Meta:
        unique_together = ['assignment', 'student']
        ordering = ['-submission_date']
    
    def __str__(self):
        return f"{self.student.username}'s submission for {self.assignment.title}"
    
    @property
    def is_late(self):
        return self.submission_date > self.assignment.due_date
