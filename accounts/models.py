"""
Models for the accounts app handling user profiles and authentication.
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta


class UserProfile(models.Model):
    """
    Extended user profile model that adds additional fields to the default Django User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_instructor = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class StudentProfile(models.Model):
    """
    Student-specific profile model for tracking academic progress and enrolled courses.
    """
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='student_profile')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    current_grade = models.FloatField(default=0.0)
    completed_courses = models.ManyToManyField('courses.Course', related_name='completed_by', blank=True)
    enrolled_courses = models.ManyToManyField('courses.Course', related_name='enrolled_students', blank=True)
    total_study_time = models.DurationField(default=timedelta(0))

    def __str__(self):
        return f"{self.user.user.username}'s Student Profile"

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to automatically create a UserProfile when a new User is created.
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=UserProfile)
def create_student_profile(sender, instance, created, **kwargs):
    """
    Signal handler to automatically create a StudentProfile when a new UserProfile is created.
    """
    if created and not instance.is_instructor:
        StudentProfile.objects.create(user=instance)