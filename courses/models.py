"""
Models for the courses app managing course content and organization.
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Course(models.Model):
    """
    Course model representing a complete educational course.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='courses', null=True, blank=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    image = models.ImageField(upload_to='courses/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)
    duration = models.DurationField(help_text="Expected duration to complete the course")
    is_active = models.BooleanField(default=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    prerequisites = models.ManyToManyField('self', 
                                         symmetrical=False,
                                         blank=True,
                                         related_name='prerequisite_for')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Module(models.Model):
    """
    Module model for organizing course content into logical sections.
    """
    course = models.ForeignKey(Course,
                             on_delete=models.CASCADE,
                             related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Content(models.Model):
    CONTENT_TYPES = (
        ('text', 'Text'),
        ('video', 'Video'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    )

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"
