"""
Admin configuration for the learning app.
"""
from django.contrib import admin
from .models import Content, Progress, Quiz


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'content_type', 'order', 'created_at']
    list_filter = ['content_type', 'module__course', 'created_at']
    search_fields = ['title', 'content', 'module__title']
    ordering = ['module', 'order']
    date_hierarchy = 'created_at'


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'content', 'completed', 'score', 'last_accessed']
    list_filter = ['completed', 'course', 'completion_date']
    search_fields = ['student__username', 'course__title', 'content__title']
    date_hierarchy = 'last_accessed'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['content', 'passing_score', 'time_limit']
    list_filter = ['passing_score']
    search_fields = ['content__title', 'content__module__title']
