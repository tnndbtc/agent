"""Admin configuration for novels app."""
from django.contrib import admin
from .models import (
    NovelProject, Plot, Character, Setting,
    ChapterOutline, Chapter, Example, GenerationTask
)


@admin.register(NovelProject)
class NovelProjectAdmin(admin.ModelAdmin):
    """Admin for NovelProject."""
    list_display = ['title', 'user', 'status', 'total_word_count', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['chroma_collection_name', 'created_at', 'updated_at']


@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    """Admin for Plot."""
    list_display = ['project', 'genre', 'updated_at']
    search_fields = ['project__title']


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    """Admin for Character."""
    list_display = ['name', 'role', 'project', 'updated_at']
    list_filter = ['role']
    search_fields = ['name', 'project__title']


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    """Admin for Setting."""
    list_display = ['location', 'project', 'is_primary', 'updated_at']
    list_filter = ['is_primary']


@admin.register(ChapterOutline)
class ChapterOutlineAdmin(admin.ModelAdmin):
    """Admin for ChapterOutline."""
    list_display = ['number', 'title', 'project', 'pacing']
    list_filter = ['pacing']
    search_fields = ['title', 'project__title']


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    """Admin for Chapter."""
    list_display = ['chapter_number', 'title', 'project', 'word_count', 'is_draft', 'updated_at']
    list_filter = ['is_draft', 'language', 'writing_style']
    search_fields = ['title', 'project__title']


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    """Admin for Example."""
    list_display = ['category', 'is_good', 'user', 'created_at']
    list_filter = ['is_good', 'category']


@admin.register(GenerationTask)
class GenerationTaskAdmin(admin.ModelAdmin):
    """Admin for GenerationTask."""
    list_display = ['task_type', 'status', 'progress', 'project', 'created_at']
    list_filter = ['task_type', 'status']
    readonly_fields = ['created_at', 'started_at', 'completed_at']
