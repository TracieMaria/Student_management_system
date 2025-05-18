"""
Models for grade management
"""
from django.db import models
from django.conf import settings
from courses.models import Course
from learning.assignment_models import Assignment, AssignmentSubmission

class Grade(models.Model):
    """
    Grade model for tracking student grades across courses
    """
    GRADE_CHOICES = (
        ('A', 'A (90-100%)'),
        ('B', 'B (80-89%)'),
        ('C', 'C (70-79%)'),
        ('D', 'D (60-69%)'),
        ('F', 'F (Below 60%)'),
        ('I', 'Incomplete'),
    )
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='grades', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='grades', on_delete=models.CASCADE)
    final_grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True, null=True)
    numeric_grade = models.FloatField(blank=True, null=True)
    is_passing = models.BooleanField(default=False)
    comments = models.TextField(blank=True)
    date_graded = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username}'s grade for {self.course.title}: {self.final_grade or 'Not graded'}"
    
    def calculate_grade(self):
        """Calculate the student's grade based on assignment submissions"""
        course_assignments = self.course.assignments.all()
        
        if not course_assignments:
            return None
            
        total_points_possible = sum(a.total_points for a in course_assignments)
        if total_points_possible == 0:
            return None
            
        # Get all submissions for this student for course assignments
        submissions = AssignmentSubmission.objects.filter(
            student=self.student,
            assignment__course=self.course,
            score__isnull=False
        )
        
        if not submissions:
            return 0
            
        points_earned = sum(submission.score for submission in submissions)
        grade_percentage = (points_earned / total_points_possible) * 100
        
        # Update numeric grade
        self.numeric_grade = grade_percentage
        
        # Determine letter grade
        if grade_percentage >= 90:
            self.final_grade = 'A'
            self.is_passing = True
        elif grade_percentage >= 80:
            self.final_grade = 'B'
            self.is_passing = True
        elif grade_percentage >= 70:
            self.final_grade = 'C'
            self.is_passing = True
        elif grade_percentage >= 60:
            self.final_grade = 'D'
            self.is_passing = True
        else:
            self.final_grade = 'F'
            self.is_passing = False
            
        self.save()
        return grade_percentage
