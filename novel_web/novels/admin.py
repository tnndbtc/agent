"""Admin configuration for novels app."""
from django.contrib import admin
from .models import (
    NovelProject, Plot, Character, Setting,
    Chapter, Example, GenerationTask,
    ScoreCategory, ScoreCategoryTranslation, ExampleScore,
    SystemPolicy, SystemPolicyTranslation,
    AgentRole, AgentRoleTranslation,
    WritingStyle, WritingStyleTranslation,
    WritingTechnique, WritingTechniqueTranslation
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
    list_display = ['project', 'updated_at']
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


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    """Admin for Chapter."""
    list_display = ['chapter_number', 'title', 'project', 'word_count', 'is_draft', 'updated_at']
    list_filter = ['is_draft', 'language', 'writing_style']
    search_fields = ['title', 'project__title']


class ScoreCategoryTranslationInline(admin.TabularInline):
    """Inline admin for ScoreCategoryTranslation."""
    model = ScoreCategoryTranslation
    extra = 0
    fields = ['language_code', 'name']


@admin.register(ScoreCategory)
class ScoreCategoryAdmin(admin.ModelAdmin):
    """Admin for ScoreCategory."""
    list_display = ['id', 'name', 'public', 'is_system', 'created_by', 'default_weight', 'order', 'created_at']
    list_filter = ['public', 'is_system']
    search_fields = ['name', 'name_key']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ScoreCategoryTranslationInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'public', 'created_by')
        }),
        ('System Category Fields', {
            'fields': ('is_system', 'name_key', 'default_weight', 'order'),
            'description': 'These fields are only for system-defined categories'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class ExampleScoreInline(admin.TabularInline):
    """Inline admin for ExampleScore."""
    model = ExampleScore
    extra = 0
    fields = ['category', 'weight', 'score', 'weighted_score']
    readonly_fields = ['weighted_score']


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    """Admin for Example."""
    list_display = ['category', 'is_good', 'public', 'user', 'total_score', 'created_at']
    list_filter = ['is_good', 'category', 'public']
    search_fields = ['content', 'description']
    readonly_fields = ['total_score', 'created_at']
    inlines = [ExampleScoreInline]


@admin.register(GenerationTask)
class GenerationTaskAdmin(admin.ModelAdmin):
    """Admin for GenerationTask."""
    list_display = ['task_type', 'status', 'progress', 'project', 'created_at']
    list_filter = ['task_type', 'status']
    readonly_fields = ['created_at', 'started_at', 'completed_at']


# ========================================
# Prompt Architecture Admin (5-Layer)
# ========================================

class SystemPolicyTranslationInline(admin.TabularInline):
    """Inline admin for SystemPolicyTranslation."""
    model = SystemPolicyTranslation
    extra = 0
    fields = ['language_code', 'content']


@admin.register(SystemPolicy)
class SystemPolicyAdmin(admin.ModelAdmin):
    """Admin for SystemPolicy."""
    list_display = ['name_key', 'policy_type', 'is_active', 'priority', 'created_at']
    list_filter = ['policy_type', 'is_active']
    search_fields = ['name_key']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SystemPolicyTranslationInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_key', 'policy_type', 'is_active', 'priority')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class AgentRoleTranslationInline(admin.TabularInline):
    """Inline admin for AgentRoleTranslation."""
    model = AgentRoleTranslation
    extra = 0
    fields = ['language_code', 'system_prompt']


@admin.register(AgentRole)
class AgentRoleAdmin(admin.ModelAdmin):
    """Admin for AgentRole."""
    list_display = ['name_key', 'module_name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name_key', 'module_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AgentRoleTranslationInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_key', 'module_name', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class WritingStyleTranslationInline(admin.TabularInline):
    """Inline admin for WritingStyleTranslation."""
    model = WritingStyleTranslation
    extra = 0
    fields = ['language_code', 'name', 'description', 'instructions']


@admin.register(WritingStyle)
class WritingStyleAdmin(admin.ModelAdmin):
    """Admin for WritingStyle."""
    list_display = ['name_key', 'is_system', 'created_by', 'public', 'pacing', 'created_at']
    list_filter = ['is_system', 'public', 'pacing', 'paragraph_length', 'dialogue_ratio']
    search_fields = ['name_key', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WritingStyleTranslationInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_key', 'is_system', 'created_by', 'public')
        }),
        ('Style Parameters', {
            'fields': ('pacing', 'tone', 'paragraph_length', 'dialogue_ratio', 'cliffhanger_enabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class WritingTechniqueTranslationInline(admin.TabularInline):
    """Inline admin for WritingTechniqueTranslation."""
    model = WritingTechniqueTranslation
    extra = 0
    fields = ['language_code', 'name', 'description', 'instructions']


@admin.register(WritingTechnique)
class WritingTechniqueAdmin(admin.ModelAdmin):
    """Admin for WritingTechnique."""
    list_display = ['name_key', 'is_system', 'created_by', 'public', 'category', 'created_at']
    list_filter = ['is_system', 'public', 'category']
    search_fields = ['name_key', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WritingTechniqueTranslationInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_key', 'is_system', 'created_by', 'public', 'category')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
