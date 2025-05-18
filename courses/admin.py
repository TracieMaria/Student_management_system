"""
Admin configuration for the courses app.
"""
from django.contrib import admin
from .models import Course, Module


class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'instructor']
    search_fields = ['title', 'description', 'instructor__username']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]
    date_hierarchy = 'created_at'


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']
    search_fields = ['title', 'description', 'course__title']
    ordering = ['course', 'order']
